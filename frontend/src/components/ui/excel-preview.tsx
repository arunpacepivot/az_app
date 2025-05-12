import React, { useState, useMemo, useEffect, useCallback } from 'react'
import {
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  ColumnDef,
  FilterFn,
  SortingState,
  PaginationState,
  ColumnResizeMode,
} from '@tanstack/react-table'
import { useVirtualizer } from '@tanstack/react-virtual'
import { rankItem } from '@tanstack/match-sorter-utils'
import { ArrowDownTrayIcon, MagnifyingGlassIcon, XCircleIcon } from '@heroicons/react/24/outline'
import { ArrowsUpDownIcon } from '@heroicons/react/24/solid'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetClose,
} from '@/components/ui/sheet'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Loader2 } from 'lucide-react'

// For fuzzy search functionality
declare module '@tanstack/table-core' {
  interface FilterFns {
    fuzzy: FilterFn<unknown>
  }
  interface FilterMeta {
    itemRank: RankingInfo
  }
}

interface RankingInfo {
  rankedValue: any
  rank: number
  passed: boolean
}

const fuzzyFilter: FilterFn<any> = (row, columnId, value, addMeta) => {
  const itemRank = rankItem(row.getValue(columnId), value)
  addMeta({ itemRank })
  return itemRank.passed
}

interface ExcelPreviewProps {
  data: Record<string, Array<Record<string, any>>>
  isOpen: boolean
  onOpenChange: (open: boolean) => void
  onDownload: () => void
}

const LoadingSpinner = () => (
  <div className="h-full w-full flex items-center justify-center">
    <Loader2 className="h-8 w-8 text-yellow-400 animate-spin" />
  </div>
);

export function ExcelPreview({ data, isOpen, onOpenChange, onDownload }: ExcelPreviewProps) {
  const [activeSheet, setActiveSheet] = useState<string>(() => {
    const sheets = Object.keys(data)
    return sheets.length > 0 ? sheets[0] : ''
  })
  
  const [globalFilter, setGlobalFilter] = useState('')
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  })
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnResizeMode] = useState<ColumnResizeMode>('onChange')
  const [columnSizing, setColumnSizing] = useState({})
  const [isLoading, setIsLoading] = useState(true)
  const [hoveredCell, setHoveredCell] = useState<string | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)

  // Initialize component when first opened with data
  useEffect(() => {
    if (isOpen && !isInitialized && Object.keys(data).length > 0) {
      setIsLoading(true);
      
      // Check if the active sheet exists and get its row count
      const activeSheetData = activeSheet && data[activeSheet] ? data[activeSheet] : [];
      const rowCount = activeSheetData.length;
      
      // Use a shorter or no timeout for small datasets
      if (rowCount === 0) {
        // No rows, no need for loading
        setIsInitialized(true);
        setIsLoading(false);
      } else if (rowCount <= 25) {
        // Small dataset, use a very short timeout
        setTimeout(() => {
          setIsInitialized(true);
          setIsLoading(false);
        }, 50);
      } else {
        // Larger dataset, use the regular timeout
        setTimeout(() => {
          setIsInitialized(true);
          setIsLoading(false);
        }, 300);
      }
    }
  }, [isOpen, data, isInitialized, activeSheet]);

  // Reset initialization state when closed
  useEffect(() => {
    if (!isOpen) {
      setIsInitialized(false);
    }
  }, [isOpen]);

  // Handle sheet change with loading state - use longer timeouts and a two-phase approach
  const handleSheetChange = useCallback((sheetName: string) => {
    if (sheetName !== activeSheet) {
      setIsLoading(true);
      
      // Check the target sheet's row count
      const targetSheetData = data[sheetName] || [];
      const rowCount = targetSheetData.length;
      
      // Phase 1: Update the active sheet with a delay based on dataset size
      if (rowCount === 0) {
        // No rows, minimal delay
        setActiveSheet(sheetName);
        setSorting([]);
        setGlobalFilter('');
        setPagination({
          pageIndex: 0,
          pageSize: 20,
        });
        setColumnSizing({});
        setHoveredCell(null);
        setIsLoading(false);
      } else if (rowCount <= 25) {
        // Small dataset, shorter delays
        setTimeout(() => {
          setActiveSheet(sheetName);
          setSorting([]);
          setGlobalFilter('');
          setPagination({
            pageIndex: 0,
            pageSize: 20,
          });
          setColumnSizing({});
          setHoveredCell(null);
          setIsLoading(false);
        }, 50);
      } else {
        // Larger dataset, use the multi-phase approach
        setTimeout(() => {
          // Important: Keep the loading state true during this first phase
          setActiveSheet(sheetName);
          
          // Phase 2: Finalize any calculations and state updates after another delay
          setTimeout(() => {
            // Completely reset ALL table state to avoid column ID references from previous sheets
            setSorting([]);
            setGlobalFilter('');
            setPagination({
              pageIndex: 0,
              pageSize: 20,
            });
            setColumnSizing({});
            setHoveredCell(null);
            
            // Create a small delay before turning off loading to ensure state is fully reset
            setTimeout(() => {
              setIsLoading(false);
            }, 150);
          }, 150);
        }, 200);
      }
    }
  }, [activeSheet, data]);

  // Create columns based on the first row of data
  const columns = useMemo(() => {
    if (!activeSheet || !data[activeSheet] || data[activeSheet].length === 0) {
      return []
    }

    const firstRow = data[activeSheet][0]
    return Object.keys(firstRow).map((key) => ({
      accessorKey: key,
      header: key,
      minSize: 100,
      maxSize: 500,
      size: Math.max(150, Math.min(250, key.length * 10)),
      enableResizing: true,
    })) as ColumnDef<any>[]
  }, [activeSheet, data])

  const sheetData = useMemo(() => {
    return activeSheet && data[activeSheet] ? data[activeSheet] : []
  }, [activeSheet, data])

  const table = useReactTable({
    data: sheetData,
    columns,
    filterFns: {
      fuzzy: fuzzyFilter,
    },
    state: {
      globalFilter,
      pagination,
      sorting,
      columnSizing,
    },
    onColumnSizingChange: setColumnSizing,
    columnResizeMode,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onGlobalFilterChange: setGlobalFilter,
    onPaginationChange: setPagination,
    onSortingChange: setSorting,
    enableColumnResizing: true,
  })

  // Set up virtualization
  const { rows } = table.getRowModel()
  const parentRef = React.useRef<HTMLDivElement>(null)
  
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 35, // approximate row height
    overscan: 5,
  })

  const paddingTop = rowVirtualizer.getVirtualItems().length > 0
    ? rowVirtualizer.getVirtualItems()[0].start
    : 0

  const paddingBottom = rowVirtualizer.getVirtualItems().length > 0
    ? rowVirtualizer.getTotalSize() - rowVirtualizer.getVirtualItems()[rowVirtualizer.getVirtualItems().length - 1].end
    : 0

  // If no sheets are available, don't render anything
  if (Object.keys(data).length === 0) {
    return null
  }

  // Define optimized tooltip renderer that only renders when needed
  const renderCellWithOptionalTooltip = (cellValue: string, cellId: string, rowIndex: number) => {
    // Simplified condition - show tooltips for any non-empty text
    const needsTooltip = cellValue && cellValue.length > 10;
    const isHovered = hoveredCell === cellId;
    // Use bottom side for first few rows, top for the rest
    const tooltipSide = rowIndex < 2 ? "bottom" : "top";

    if (isHovered && needsTooltip) {
      return (
        <TooltipProvider delayDuration={100}>
          <Tooltip open={true}>
            <TooltipTrigger asChild>
              <div className="truncate cursor-pointer text-white">{cellValue}</div>
            </TooltipTrigger>
            <TooltipContent 
              side={tooltipSide}
              align="start"
              sideOffset={5}
              className="bg-gray-800 text-white border border-yellow-400 px-3 py-2 max-w-xs break-words z-[100]"
            >
              {cellValue}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    }
    
    return <div className={`truncate ${needsTooltip ? "cursor-pointer" : ""} text-white`}>{cellValue}</div>;
  };

  // Custom empty state component with a better message
  const EmptyState = () => (
    <div className="flex flex-col flex-1 w-full h-full items-center justify-center" style={{ minHeight: '300px' }}>
      <div className="py-12 px-10 rounded-lg bg-gray-800/50 border border-gray-700 shadow-xl flex flex-col items-center justify-center max-w-md w-full">
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          className="h-20 w-20 text-yellow-400/50 mb-6" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={1.5} 
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
          />
        </svg>
        <h3 className="text-2xl font-medium text-yellow-400 mb-3 text-center">No data available</h3>
        <p className="text-base text-gray-400 text-center">This sheet contains no rows to display</p>
      </div>
    </div>
  );

  return (
    <Sheet open={isOpen} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[90%] max-w-none sm:max-w-none bg-gray-900 border-l border-gray-700 p-0 overflow-hidden">
        <div className="h-full flex flex-col">
          <SheetHeader className="p-6 border-b border-gray-700 flex-shrink-0">
            <div className="flex justify-between items-center">
              <SheetTitle className="text-2xl text-yellow-400">Excel Data Preview</SheetTitle>
              <div className="flex items-center space-x-2">
                <Button
                  onClick={onDownload}
                  className="bg-green-600 text-white hover:bg-green-500"
                >
                  <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                  Download Excel
                </Button>
                <SheetClose asChild>
                  <Button variant="outline" size="icon" className="h-8 w-8 border-gray-700 bg-gray-800 hover:bg-gray-700">
                    <XCircleIcon className="h-5 w-5 text-white" />
                  </Button>
                </SheetClose>
              </div>
            </div>
            <SheetDescription className="text-gray-400">
              Preview and analyze the optimized data before download
            </SheetDescription>
          </SheetHeader>

          <div className="flex-1 flex flex-col overflow-hidden">
            <Tabs value={activeSheet} onValueChange={handleSheetChange} className="h-full flex flex-col">
              <div className="px-4 pt-4 overflow-x-auto flex-shrink-0 scrollbar-hide">
                <TabsList className="bg-gray-800 border border-gray-700 p-1 inline-flex w-auto">
                  {Object.keys(data).map((sheetName) => (
                    <TabsTrigger
                      key={sheetName}
                      value={sheetName}
                      className="data-[state=active]:bg-yellow-400 data-[state=active]:text-gray-900 text-white"
                      disabled={isLoading}
                    >
                      {sheetName}
                    </TabsTrigger>
                  ))}
                </TabsList>
              </div>

              {isLoading ? (
                <div className="flex-1 flex items-center justify-center">
                  <LoadingSpinner />
                </div>
              ) : (
                <>
                  <div className="px-4 pt-4 pb-2 flex-shrink-0">
                    <div className="flex items-center justify-between">
                      <div className="relative w-72">
                        <MagnifyingGlassIcon className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                        <Input
                          placeholder="Search all columns..."
                          value={globalFilter ?? ''}
                          onChange={(e) => setGlobalFilter(e.target.value)}
                          className="pl-8 bg-gray-800 border-gray-700 text-white"
                        />
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <p className="text-sm text-white">
                          {table.getFilteredRowModel().rows.length} row(s)
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex-1 px-4 pb-4 overflow-hidden flex flex-col">
                    <TabsContent 
                      value={activeSheet} 
                      className="flex-1 flex flex-col overflow-hidden h-full"
                    >
                      {rows.length > 0 ? (
                        // Show table with data
                        <div className="flex-1 rounded-md border border-gray-700 overflow-hidden">
                          <div 
                            ref={parentRef}
                            className="overflow-auto h-full custom-scrollbar"
                          >
                            <div className="inline-block min-w-full">
                              <div 
                                className="w-full relative"
                                style={{
                                  width: table.getTotalSize(),
                                }}
                              >
                                <div className="sticky top-0 z-10 bg-gray-800 border-b border-gray-700">
                                  {table.getHeaderGroups().map((headerGroup) => (
                                    <div key={headerGroup.id} className="flex">
                                      {headerGroup.headers.map((header) => (
                                        <div
                                          key={header.id}
                                          className="relative group cursor-pointer"
                                          style={{
                                            width: header.getSize(),
                                          }}
                                          onClick={() => header.column.toggleSorting(header.column.getIsSorted() === 'asc')}
                                        >
                                          <div 
                                            className="text-left text-yellow-400 font-medium px-3 py-3 whitespace-nowrap overflow-hidden text-ellipsis"
                                          >
                                            <div className="flex items-center group">
                                              <div className="truncate mr-2">
                                                {String(header.column.columnDef.header)}
                                              </div>
                                              <ArrowsUpDownIcon className="h-4 w-4 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </div>
                                          </div>
                                          {header.column.getCanResize() && (
                                            <div
                                              onMouseDown={header.getResizeHandler()}
                                              onTouchStart={header.getResizeHandler()}
                                              className={`absolute top-0 right-0 h-full w-1.5 cursor-col-resize select-none touch-none bg-yellow-400 opacity-0 hover:opacity-100 ${
                                                header.column.getIsResizing() ? 'opacity-100' : ''
                                              }`}
                                            ></div>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  ))}
                                </div>
                                
                                <div className="bg-gray-900 relative">
                                  <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, width: '100%', position: 'relative' }}>
                                    <div style={{ 
                                      position: 'absolute', 
                                      top: 0, 
                                      left: 0, 
                                      width: '100%', 
                                      transform: `translateY(${paddingTop}px)` 
                                    }}>
                                      {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                                        const row = rows[virtualRow.index];
                                        return (
                                          <div key={row.id} className="flex border-b border-gray-700 hover:bg-gray-800/60">
                                            {row.getVisibleCells().map((cell) => {
                                              const cellId = `${row.id}-${cell.id}`;
                                              const cellValue = String(cell.getValue() || '');
                                              return (
                                                <div
                                                  key={cell.id}
                                                  className="text-white px-3 py-2 whitespace-nowrap overflow-hidden text-ellipsis"
                                                  style={{
                                                    width: cell.column.getSize(),
                                                    height: '35px',
                                                  }}
                                                  onMouseEnter={() => {
                                                    if (cellValue && cellValue.length > 10) {
                                                      setHoveredCell(cellId);
                                                    }
                                                  }}
                                                  onMouseLeave={() => setHoveredCell(null)}
                                                >
                                                  {renderCellWithOptionalTooltip(cellValue, cellId, virtualRow.index)}
                                                </div>
                                              );
                                            })}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        // Show empty state for the entire content area
                        <div className="flex-1 rounded-md border border-gray-700 overflow-hidden bg-gray-900">
                          <div className="flex items-center justify-center h-full">
                            <div className="py-10 px-8 rounded-lg bg-gray-800/50 border border-gray-700 shadow-xl text-center max-w-md">
                              <svg 
                                xmlns="http://www.w3.org/2000/svg" 
                                className="h-16 w-16 mx-auto text-yellow-400/50 mb-4" 
                                fill="none" 
                                viewBox="0 0 24 24" 
                                stroke="currentColor"
                              >
                                <path 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round" 
                                  strokeWidth={1.5} 
                                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
                                />
                              </svg>
                              <h3 className="text-xl font-medium text-yellow-400 mb-2">No data available</h3>
                              <p className="text-sm text-gray-400">This sheet contains no rows to display</p>
                            </div>
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between space-x-2 mt-4 flex-shrink-0">
                        <div className="flex items-center space-x-2">
                          <p className="text-sm text-white">
                            {table.getPageCount() > 0 ? 
                              `Page ${table.getState().pagination.pageIndex + 1} of ${table.getPageCount()}` : 
                              'No pages available'}
                          </p>
                          {table.getPageCount() > 0 && (
                            <Select
                              value={String(table.getState().pagination.pageSize)}
                              onValueChange={(value) => {
                                table.setPageSize(Number(value))
                              }}
                            >
                              <SelectTrigger className="h-8 w-[80px] bg-gray-800 border-gray-700 text-white">
                                <SelectValue placeholder={table.getState().pagination.pageSize} />
                              </SelectTrigger>
                              <SelectContent className="bg-gray-800 border-gray-700">
                                {[10, 20, 50, 100].map((pageSize) => (
                                  <SelectItem key={pageSize} value={String(pageSize)} className="text-white">
                                    {pageSize}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="outline"
                            className="h-8 w-8 p-0 border-gray-700 text-white"
                            onClick={() => table.previousPage()}
                            disabled={!table.getCanPreviousPage() || table.getPageCount() === 0}
                          >
                            <span className="sr-only">Go to previous page</span>
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                            </svg>
                          </Button>
                          <Button
                            variant="outline"
                            className="h-8 w-8 p-0 border-gray-700 text-white"
                            onClick={() => table.nextPage()}
                            disabled={!table.getCanNextPage() || table.getPageCount() === 0}
                          >
                            <span className="sr-only">Go to next page</span>
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </Button>
                        </div>
                      </div>
                    </TabsContent>
                  </div>
                </>
              )}
            </Tabs>
          </div>
        </div>

        <style jsx global>{`
          .custom-scrollbar::-webkit-scrollbar {
            width: 6px;
            height: 6px;
          }
          
          .custom-scrollbar::-webkit-scrollbar-track {
            background: rgba(31, 41, 55, 0.5);
            border-radius: 4px;
          }
          
          .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(107, 114, 128, 0.5);
            border-radius: 4px;
            border: 1px solid rgba(234, 179, 8, 0.1);
          }
          
          .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(234, 179, 8, 0.3);
          }
          
          .scrollbar-hide::-webkit-scrollbar {
            display: none;
          }
          
          .scrollbar-hide {
            -ms-overflow-style: none;
            scrollbar-width: none;
          }
        `}</style>
      </SheetContent>
    </Sheet>
  )
} 