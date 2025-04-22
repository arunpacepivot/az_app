import React, { useState, useMemo, useRef, useEffect, memo } from 'react'
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  FilterFn,
  Row,
  getGroupedRowModel,
  getExpandedRowModel,
  ColumnResizeMode
} from '@tanstack/react-table'
import { rankItem } from '@tanstack/match-sorter-utils'

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  DropdownMenu, 
  DropdownMenuCheckboxItem, 
  DropdownMenuContent, 
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { 
  ChevronDown, 
  ChevronsUpDown, 
  ChevronUp, 
  Download, 
  Search, 
  SlidersHorizontal, 
  Filter,
  X,
  ChevronRight,
  Layers,
} from 'lucide-react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card'
import { Popover, PopoverContent, PopoverTrigger } from './popover'
import { Separator } from './separator'
import { cn } from '@/lib/utils'

// Define fuzzy filter
const fuzzyFilter: FilterFn<any> = (row, columnId, value, addMeta) => {
  const itemRank = rankItem(row.getValue(columnId), value)
  return itemRank.passed
}

// Define range filter
const betweenFilter: FilterFn<any> = (row, columnId, value, addMeta) => {
  const rowValue = row.getValue(columnId) as any
  const [min, max] = value as [string, string]
  
  // Handle empty values
  if (min === '' && max === '') return true
  if (min === '' && rowValue <= max) return true
  if (max === '' && rowValue >= min) return true
  
  // Regular between filter
  return rowValue >= min && rowValue <= max
}

// Define equality filter
const equalityFilter: FilterFn<any> = (row, columnId, value, addMeta) => {
  return row.getValue(columnId) === value
}

interface DataTableProps<TData, TValue> {
  title?: string
  description?: string
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  onDownload?: () => void
  enableSorting?: boolean
  enableFiltering?: boolean
  enableColumnVisibility?: boolean
  enablePagination?: boolean
  enableGrouping?: boolean
  enableColumnResizing?: boolean
}

interface FilterOption {
  label: string;
  value: string;
}

const filterOptions: FilterOption[] = [
  { label: 'Contains', value: 'contains' },
  { label: 'Equals', value: 'equals' },
  { label: 'Starts With', value: 'startsWith' },
  { label: 'Ends With', value: 'endsWith' },
  { label: 'Between', value: 'between' },
  { label: 'Greater Than', value: 'gt' },
  { label: 'Less Than', value: 'lt' },
]

// CSS for custom scrollbar
const customScrollbarCSS = `
.scrollbar-custom::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
.scrollbar-custom::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.1);
  border-radius: 8px;
}
.scrollbar-custom::-webkit-scrollbar-thumb {
  background: rgba(107, 114, 128, 0.5);
  border-radius: 8px;
}
.scrollbar-custom::-webkit-scrollbar-thumb:hover {
  background: rgba(107, 114, 128, 0.8);
}
.scrollbar-custom::-webkit-scrollbar-corner {
  background: transparent;
}

/* Bottom scrollbar specific styles */
.table-container {
  position: relative;
  overflow-x: auto;
  border-radius: 0.375rem;
  border: 1px solid hsl(var(--border));
  scrollbar-width: thin;
  display: block;
  width: 100%;
}

/* Custom scrollbar styling specifically for the table container */
.table-container::-webkit-scrollbar {
  height: 12px; /* Increased height for better visibility */
  width: 12px;
}
.table-container::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.3);
  border-radius: 0;
}
.table-container::-webkit-scrollbar-thumb {
  background-color: rgba(107, 114, 128, 0.7);
  border-radius: 6px;
  border: 3px solid rgba(31, 41, 55, 0.3);
  background-clip: padding-box;
}
.table-container::-webkit-scrollbar-thumb:hover {
  background-color: rgba(107, 114, 128, 0.9);
  border: 3px solid rgba(31, 41, 55, 0.3);
  background-clip: padding-box;
}
.table-container .data-table {
  min-width: 100%;
  width: max-content;
  border: none; /* Remove inner table border */
}
/* Remove table border when in container */
.table-container > table {
  margin: 0;
  border: none;
}
`;

// Create a separate FilterInput component to maintain focus
const FilterInput = memo(({ 
  column, 
  filterType, 
  columnFilterValue, 
  onFilterChange, 
  inputType = 'text',
  placeholder = '',
  className = 'max-w-sm'
}: { 
  column: any;
  filterType: string;
  columnFilterValue: any;
  onFilterChange: (value: any) => void;
  inputType?: string;
  placeholder?: string;
  className?: string;
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  
  const stopPropagation = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
  };
  
  return (
    <Input
      ref={inputRef}
      key={`filter-input-${column.id}-${filterType}`}
      value={(columnFilterValue ?? '') as string}
      onChange={e => onFilterChange(e.target.value)}
      className={className}
      placeholder={placeholder}
      type={inputType}
      onClick={stopPropagation}
      onKeyDown={stopPropagation}
    />
  );
});

FilterInput.displayName = 'FilterInput';

// Filter renderer based on the filter type
function FilterRenderer({
  column,
  filterType,
  onFilterChange,
  onTypeChange,
}: {
  column: any
  filterType: string
  onFilterChange: (value: any) => void
  onTypeChange: (value: string) => void
}) {
  const columnFilterValue = column.getFilterValue()
  
  switch (filterType) {
    case 'contains':
    case 'equals':
    case 'startsWith':
    case 'endsWith':
      return (
        <FilterInput
          column={column}
          filterType={filterType}
          columnFilterValue={columnFilterValue}
          onFilterChange={onFilterChange}
          placeholder={`Filter ${column.id}...`}
        />
      )
    case 'between':
      return (
        <div className="flex gap-2 items-center">
          <FilterInput
            column={column}
            filterType={filterType}
            columnFilterValue={columnFilterValue?.[0] ?? ''}
            onFilterChange={(value) => onFilterChange([value, columnFilterValue?.[1] ?? ''])}
            inputType={typeof column.getFacetedRowModel().rows[0]?.getValue(column.id) === 'number' ? 'number' : 'text'}
            placeholder="Min"
            className="max-w-[80px]"
          />
          <span>to</span>
          <FilterInput
            column={column}
            filterType={filterType}
            columnFilterValue={columnFilterValue?.[1] ?? ''}
            onFilterChange={(value) => onFilterChange([columnFilterValue?.[0] ?? '', value])}
            inputType={typeof column.getFacetedRowModel().rows[0]?.getValue(column.id) === 'number' ? 'number' : 'text'}
            placeholder="Max"
            className="max-w-[80px]"
          />
        </div>
      )
    case 'gt':
    case 'lt':
      return (
        <FilterInput
          column={column}
          filterType={filterType}
          columnFilterValue={columnFilterValue}
          onFilterChange={onFilterChange}
          inputType={typeof column.getFacetedRowModel().rows[0]?.getValue(column.id) === 'number' ? 'number' : 'text'}
          placeholder={filterType === 'gt' ? 'Greater than...' : 'Less than...'}
        />
      )
    default:
      return null
  }
}

// Create a separate FilterTypeSelect component
const FilterTypeSelect = memo(({ 
  column, 
  value, 
  onChange, 
  onOpenChange
}: { 
  column: any;
  value: string;
  onChange: (value: string) => void;
  onOpenChange: (open: boolean) => void;
}) => {
  const stopPropagation = (e: React.MouseEvent) => {
    e.stopPropagation();
  };
  
  return (
    <Select
      value={value}
      onValueChange={onChange}
      onOpenChange={onOpenChange}
    >
      <SelectTrigger 
        className="h-7"
        onClick={stopPropagation}
      >
        <SelectValue placeholder="Filter type" />
      </SelectTrigger>
      <SelectContent 
        align="end"
        className="z-[100]"
        position="popper"
        sideOffset={5}
        key={`filter-select-${column.id}`}
      >
        {filterOptions.map((option) => (
          <SelectItem 
            key={option.value} 
            value={option.value}
            onMouseDown={stopPropagation}
          >
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
});

FilterTypeSelect.displayName = 'FilterTypeSelect';

// Create a separate FilterPanel component
const FilterPanel = memo(({
  column,
  isFiltered,
  filterType,
  onFilterTypeChange,
  onFilterValueChange,
  onClearFilter,
  isSelecting,
  setIsSelecting
}: {
  column: any;
  isFiltered: boolean;
  filterType: string;
  onFilterTypeChange: (value: string) => void;
  onFilterValueChange: (value: any) => void;
  onClearFilter: () => void;
  isSelecting: boolean;
  setIsSelecting: (value: boolean) => void;
}) => {
  const stopPropagation = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
    e.preventDefault();
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex justify-between items-center">
        <span className="text-xs font-medium">Filter {column.id}</span>
        {isFiltered && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2"
            onClick={(e) => {
              stopPropagation(e);
              onClearFilter();
            }}
          >
            <X className="h-3 w-3" />
            <span className="sr-only">Clear filter</span>
          </Button>
        )}
      </div>
      
      <FilterTypeSelect
        column={column}
        value={filterType}
        onChange={(value) => {
          setIsSelecting(true);
          onFilterTypeChange(value);
          // Small delay to ensure the popup doesn't close
          setTimeout(() => setIsSelecting(false), 100);
        }}
        onOpenChange={(open) => {
          setIsSelecting(open);
        }}
      />
      
      <FilterRenderer
        column={column}
        filterType={filterType}
        onFilterChange={(value) => {
          onFilterValueChange(value);
        }}
        onTypeChange={(value) => {
          onFilterTypeChange(value);
        }}
      />
    </div>
  );
});

FilterPanel.displayName = 'FilterPanel';

export function DataTable<TData, TValue>({
  title,
  description,
  columns,
  data,
  onDownload,
  enableSorting = true,
  enableFiltering = true,
  enableColumnVisibility = true,
  enablePagination = true,
  enableGrouping = true,
  enableColumnResizing = true,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})
  const [globalFilter, setGlobalFilter] = useState<string>('')
  const [rowSelection, setRowSelection] = useState({})
  const [grouping, setGrouping] = useState<string[]>([])
  const [expanded, setExpanded] = useState({})
  const [columnFilterTypes, setColumnFilterTypes] = useState<Record<string, string>>({})
  const [activeFilterColumn, setActiveFilterColumn] = useState<string | null>(null)
  const [columnResizeMode] = useState<ColumnResizeMode>('onChange')

  // Add scrollbar styles to document head
  useEffect(() => {
    // Remove any existing style elements to avoid duplicates
    const existingStyle = document.getElementById('data-table-scrollbar-styles');
    if (existingStyle) {
      existingStyle.remove();
    }
    
    const styleElement = document.createElement('style');
    styleElement.id = 'data-table-scrollbar-styles';
    styleElement.textContent = customScrollbarCSS;
    document.head.appendChild(styleElement);
    
    return () => {
      if (document.getElementById('data-table-scrollbar-styles')) {
        document.getElementById('data-table-scrollbar-styles')?.remove();
      }
    };
  }, []);

  // Add resizing styles
  useEffect(() => {
    if (!document.getElementById('data-table-resize-styles')) {
      const styleEl = document.createElement('style');
      styleEl.id = 'data-table-resize-styles';
      styleEl.textContent = `
        .resizer {
          position: absolute;
          right: 0;
          top: 0;
          height: 100%;
          width: 8px; /* Wider for easier grabbing */
          background: rgba(0, 0, 0, 0.1);
          cursor: col-resize;
          user-select: none;
          touch-action: none;
          z-index: 1;
          opacity: 0;
          transition: opacity 0.2s, background-color 0.2s;
        }
        
        .resizer:hover {
          opacity: 1;
          background: rgba(255, 204, 0, 0.5);
        }
        
        .isResizing {
          opacity: 1 !important;
          background: rgba(255, 204, 0, 0.8) !important;
        }
        
        .data-table-cell {
          position: relative;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        /* Make resizing smoother */
        .data-table th,
        .data-table td {
          transition: width 0.2s ease;
        }
      `;
      document.head.appendChild(styleEl);
    }
  }, []);

  const table = useReactTable({
    data,
    columns,
    filterFns: {
      fuzzy: fuzzyFilter,
      equals: equalityFilter,
      between: betweenFilter,
    } as Record<string, FilterFn<any>>,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      globalFilter,
      grouping,
      expanded,
    },
    defaultColumn: {
      minSize: 40,
      size: 150,
      maxSize: 500,
    },
    enableColumnResizing,
    columnResizeMode,
    enableSorting,
    enableColumnFilters: enableFiltering,
    enableGlobalFilter: enableFiltering,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    onGlobalFilterChange: setGlobalFilter,
    onGroupingChange: setGrouping,
    onExpandedChange: setExpanded,
    getExpandedRowModel: getExpandedRowModel(),
    getGroupedRowModel: enableGrouping ? getGroupedRowModel() : undefined,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: enableSorting ? getSortedRowModel() : undefined,
    getFilteredRowModel: enableFiltering ? getFilteredRowModel() : undefined,
    getPaginationRowModel: enablePagination ? getPaginationRowModel() : undefined,
    globalFilterFn: fuzzyFilter,
  })

  // Function to get filter type for a column
  const getFilterTypeForColumn = (columnId: string) => {
    return columnFilterTypes[columnId] || 'contains';
  };

  // Function to set filter type for a column
  const setFilterTypeForColumn = (columnId: string, filterType: string) => {
    setColumnFilterTypes(prev => ({ ...prev, [columnId]: filterType }));
    
    // Clear existing filter when changing filter type
    const column = table.getColumn(columnId);
    if (column) {
      column.setFilterValue(undefined);
    }
  };

  // Apply appropriate filter function based on filter type
  const getFilterFnForType = (filterType: string) => {
    switch (filterType) {
      case 'contains':
        return 'fuzzy';
      case 'equals':
        return 'equals';
      case 'between':
        return 'between';
      case 'startsWith':
        return ((row: Row<any>, columnId: string, filterValue: any) => {
          const rowValue = String(row.getValue(columnId));
          return rowValue.toLowerCase().startsWith(String(filterValue).toLowerCase());
        }) as unknown as FilterFn<any>;
      case 'endsWith':
        return ((row: Row<any>, columnId: string, filterValue: any) => {
          const rowValue = String(row.getValue(columnId));
          return rowValue.toLowerCase().endsWith(String(filterValue).toLowerCase());
        }) as unknown as FilterFn<any>;
      case 'gt':
        return ((row: Row<any>, columnId: string, filterValue: any) => {
          const rowValue = row.getValue(columnId) as number;
          return rowValue > Number(filterValue);
        }) as unknown as FilterFn<any>;
      case 'lt':
        return ((row: Row<any>, columnId: string, filterValue: any) => {
          const rowValue = row.getValue(columnId) as number;
          return rowValue < Number(filterValue);
        }) as unknown as FilterFn<any>;
      default:
        return 'fuzzy';
    }
  };

  // Set the appropriate filter function for each column
  useEffect(() => {
    table.getAllColumns().forEach(column => {
      const filterType = getFilterTypeForColumn(column.id);
      column.columnDef.filterFn = getFilterFnForType(filterType) as any;
    });
  }, [table, columnFilterTypes]);

  // Close filter when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      
      // Don't close if clicking on filter controls
      if (
        target.closest('.filter-popover') || 
        target.closest('.filter-trigger') ||
        target.closest('[role="listbox"]') ||  // SelectContent elements
        target.closest('[cmdk-input]') ||      // Command input elements
        target.closest('[cmdk-list]') ||       // Command list elements
        target.closest('[role="dialog"]') ||   // Any dialog elements
        target.closest('input') ||             // Any input element
        document.querySelector('[role="combobox"][data-state="open"]') // Open Select component
      ) {
        return;
      }
      
      setActiveFilterColumn(null);
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Add this at a global level in the component
  const preventClose = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation();
    if (e.nativeEvent) {
      e.nativeEvent.stopImmediatePropagation();
    }
  };

  // Component for column header with filter
  const HeaderWithFilter = memo(({ column, header }: { column: any, header: any }) => {
    const isFiltered = column.getIsFiltered();
    const isActive = activeFilterColumn === column.id;
    
    // Create a local state to prevent closing when selecting options
    const [isSelecting, setIsSelecting] = useState(false);
    
    const handleToggleFilter = (e: React.MouseEvent) => {
      e.stopPropagation();
      setActiveFilterColumn(isActive ? null : column.id);
    };
    
    return (
      <div className="flex flex-col gap-1 w-full">
        <div className="flex items-center justify-between">
          {header.isPlaceholder ? null : (
            <div className="flex items-center gap-1">
              {enableSorting && column.getCanSort() ? (
                <div
                  className="flex items-center gap-1 cursor-pointer select-none"
                  onClick={column.getToggleSortingHandler()}
                >
                  {flexRender(
                    header.column.columnDef.header,
                    header.getContext()
                  )}
                  {{
                    asc: <ChevronUp className="ml-1 h-4 w-4" />,
                    desc: <ChevronDown className="ml-1 h-4 w-4" />,
                  }[column.getIsSorted() as string] ?? (
                    <ChevronsUpDown className="ml-1 h-4 w-4 opacity-40" />
                  )}
                </div>
              ) : (
                flexRender(
                  header.column.columnDef.header,
                  header.getContext()
                )
              )}
            </div>
          )}
          
          {enableFiltering && column.getCanFilter() && (
            <div>
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "h-6 w-6 p-0 ml-1 filter-trigger",
                  isFiltered && "text-blue-400"
                )}
                onClick={handleToggleFilter}
                title={`Filter ${column.id}`}
              >
                <Filter className="h-3.5 w-3.5" />
              </Button>
              
              {isActive && (
                <div 
                  className="scrollbar-custom absolute z-50 mt-1 right-0 rounded-md border border-gray-700 bg-gray-900 p-2 shadow-md filter-popover"
                  style={{ 
                    minWidth: '250px',
                    maxHeight: '300px',
                    overflowY: 'auto'
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                  }}
                >
                  <FilterPanel
                    column={column}
                    isFiltered={isFiltered}
                    filterType={getFilterTypeForColumn(column.id)}
                    onFilterTypeChange={(value) => {
                      setFilterTypeForColumn(column.id, value);
                    }}
                    onFilterValueChange={(value) => {
                      column.setFilterValue(value);
                    }}
                    onClearFilter={() => {
                      column.setFilterValue(undefined);
                    }}
                    isSelecting={isSelecting}
                    setIsSelecting={setIsSelecting}
                  />
                </div>
              )}
            </div>
          )}
        </div>
        
        {isFiltered && (
          <div className="text-xs text-blue-400 truncate max-w-[150px] pl-1">
            {column.getFilterValue() instanceof Array
              ? `${column.getFilterValue()[0]} to ${column.getFilterValue()[1]}`
              : String(column.getFilterValue())}
          </div>
        )}
      </div>
    );
  });

  HeaderWithFilter.displayName = 'HeaderWithFilter';

  // Generate the column size CSS variables for inline styles
  const columnSizingVars = useMemo(() => {
    const vars: { [key: string]: string } = {};
    
    table.getAllColumns().forEach(column => {
      vars[`--col-${column.id}-size`] = `${column.getSize()}px`;
    });
    
    return vars;
  }, [table.getState().columnSizing]);

  return (
    <Card className="w-full">
      {(title || description) && (
        <CardHeader>
          {title && <CardTitle>{title}</CardTitle>}
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
      )}
      <CardContent>
        <div className="flex items-center justify-between py-4">
          <div className="flex flex-1 items-center space-x-2">
            {enableFiltering && (
              <div className="relative w-72">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search in all columns..."
                  value={globalFilter ?? ''}
                  onChange={(e) => setGlobalFilter(e.target.value)}
                  className="pl-8"
                />
              </div>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {enableFiltering && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="ml-auto">
                    <Filter className="mr-2 h-4 w-4" />
                    Filters
                    {table.getState().columnFilters.length > 0 && (
                      <span className="ml-1 rounded-full bg-blue-600 px-1.5 text-xs text-white">
                        {table.getState().columnFilters.length}
                      </span>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent 
                  align="end" 
                  className="w-[200px] scrollbar-custom" 
                  style={{ maxHeight: '300px', overflowY: 'auto' }}
                  sideOffset={5}
                >
                  {table.getState().columnFilters.length > 0 ? (
                    <>
                      <div className="px-2 py-1.5 text-sm font-semibold">Active Filters</div>
                      {table.getState().columnFilters.map(filter => {
                        const column = table.getColumn(filter.id);
                        return column ? (
                          <div 
                            key={filter.id} 
                            className="px-2 py-1.5 flex items-center justify-between gap-2"
                            onClick={preventClose}
                            onMouseDown={preventClose}
                          >
                            <div className="truncate flex-1">
                              <span className="font-medium capitalize">{filter.id}:</span>{' '}
                              <span className="text-muted-foreground text-xs">
                                {filter.value instanceof Array
                                  ? `${filter.value[0]} to ${filter.value[1]}`
                                  : String(filter.value)}
                              </span>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 px-2"
                              onClick={(e) => {
                                preventClose(e);
                                column.setFilterValue(undefined);
                              }}
                            >
                              <X className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        ) : null;
                      })}
                      <Separator className="my-1" />
                      <div 
                        className="px-2 py-1.5 text-sm text-center text-red-600 cursor-pointer hover:bg-gray-800 rounded-sm"
                        onClick={(e) => {
                          preventClose(e);
                          table.resetColumnFilters();
                        }}
                        onMouseDown={preventClose}
                      >
                        Clear All Filters
                      </div>
                    </>
                  ) : (
                    <div className="px-2 py-1.5 text-sm text-muted-foreground">No active filters</div>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
            
            {enableGrouping && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="ml-auto">
                    <Layers className="mr-2 h-4 w-4" />
                    Group By
                    {grouping.length > 0 && (
                      <span className="ml-1 rounded-full bg-blue-600 px-1.5 text-xs text-white">
                        {grouping.length}
                      </span>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent 
                  align="end" 
                  className="w-[200px] scrollbar-custom" 
                  style={{ maxHeight: '300px', overflowY: 'auto' }}
                >
                  {grouping.length > 0 ? (
                    <>
                      <div className="px-2 py-1.5 text-sm font-semibold">Active Grouping</div>
                      {grouping.map(columnId => {
                        const column = table.getColumn(columnId);
                        return column ? (
                          <div key={columnId} className="px-2 py-1.5 flex items-center justify-between">
                            <span className="capitalize">{columnId}</span>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 px-2"
                              onClick={() => setGrouping(prev => prev.filter(g => g !== columnId))}
                            >
                              <X className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        ) : null;
                      })}
                      <Separator className="my-1" />
                    </>
                  ) : (
                    <div className="px-2 py-1.5 text-sm text-muted-foreground">No active grouping</div>
                  )}
                  <div className="px-2 py-1.5 text-sm font-semibold">Group By Column</div>
                  {table.getAllLeafColumns()
                    .filter(column => column.id !== 'actions' && !grouping.includes(column.id))
                    .map(column => (
                      <div 
                        key={column.id} 
                        className="px-2 py-1.5 text-sm cursor-pointer hover:bg-gray-800 rounded-sm"
                        onClick={() => setGrouping(prev => [...prev, column.id])}
                      >
                        <span className="capitalize">{column.id}</span>
                      </div>
                    ))}
                  {grouping.length > 0 && (
                    <>
                      <Separator className="my-1" />
                      <div 
                        className="px-2 py-1.5 text-sm text-center text-red-600 cursor-pointer hover:bg-gray-800 rounded-sm"
                        onClick={() => setGrouping([])}
                      >
                        Clear All Grouping
                      </div>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
            
            {enableColumnVisibility && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="ml-auto">
                    <SlidersHorizontal className="mr-2 h-4 w-4" />
                    Columns
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent 
                  align="end" 
                  className="scrollbar-custom" 
                  style={{ maxHeight: '300px', overflowY: 'auto' }}
                >
                  {table
                    .getAllColumns()
                    .filter((column) => column.getCanHide())
                    .map((column) => {
                      return (
                        <DropdownMenuCheckboxItem
                          key={column.id}
                          className="capitalize"
                          checked={column.getIsVisible()}
                          onCheckedChange={(value) =>
                            column.toggleVisibility(!!value)
                          }
                        >
                          {column.id}
                        </DropdownMenuCheckboxItem>
                      )
                    })}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
            {onDownload && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={onDownload}
              >
                <Download className="mr-2 h-4 w-4" />
                Download
              </Button>
            )}
          </div>
        </div>
        <div className="table-container">
          <Table className="data-table" style={columnSizingVars}>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead 
                      key={header.id} 
                      className="px-4 py-3 relative"
                      style={{ width: header.column.getSize() !== 150 ? `${header.column.getSize()}px` : undefined }}
                    >
                      <div className="flex items-center justify-between data-table-cell">
                        <HeaderWithFilter 
                          column={header.column}
                          header={header}
                        />
                        
                        {enableColumnResizing && header.column.getCanResize() && (
                          <div 
                            className={`resizer ${header.column.getIsResizing() ? 'isResizing' : ''}`}
                            onMouseDown={header.getResizeHandler()}
                            onTouchStart={header.getResizeHandler()}
                            title="Resize column"
                          />
                        )}
                      </div>
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row) => (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <TableCell 
                        key={cell.id}
                        className="p-3 data-table-cell"
                        style={{ width: cell.column.getSize() !== 150 ? `${cell.column.getSize()}px` : undefined }}
                      >
                        {cell.getIsGrouped() ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              row.toggleExpanded()
                            }}
                            className="p-1"
                          >
                            {row.getIsExpanded() ? (
                              <ChevronDown className="h-4 w-4 mr-1" />
                            ) : (
                              <ChevronRight className="h-4 w-4 mr-1" />
                            )}
                            {flexRender(
                              cell.column.columnDef.cell,
                              cell.getContext()
                            )}{' '}
                            ({row.subRows.length})
                          </Button>
                        ) : cell.getIsAggregated() ? (
                          flexRender(
                            cell.column.columnDef.aggregatedCell ??
                              cell.column.columnDef.cell,
                            cell.getContext()
                          )
                        ) : cell.getIsPlaceholder() ? null : (
                          flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext()
                          )
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={columns.length} className="h-24 text-center">
                    No results.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
        {enablePagination && (
          <div className="flex items-center justify-between space-x-2 py-4">
            <div className="text-sm text-muted-foreground">
              {Object.keys(rowSelection).length > 0 && (
                <span>{Object.keys(rowSelection).length} row{Object.keys(rowSelection).length === 1 ? '' : 's'} selected</span>
              )}
            </div>
            <div className="flex items-center space-x-6 lg:space-x-8">
              <div className="flex items-center space-x-2">
                <p className="text-sm font-medium">Rows per page</p>
                <Select
                  value={`${table.getState().pagination.pageSize}`}
                  onValueChange={(value) => {
                    table.setPageSize(Number(value))
                  }}
                >
                  <SelectTrigger className="h-8 w-[70px]">
                    <SelectValue placeholder={table.getState().pagination.pageSize} />
                  </SelectTrigger>
                  <SelectContent side="top">
                    {[10, 20, 30, 40, 50].map((pageSize) => (
                      <SelectItem key={pageSize} value={`${pageSize}`}>
                        {pageSize}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex w-[100px] items-center justify-center text-sm font-medium">
                Page {table.getState().pagination.pageIndex + 1} of{" "}
                {table.getPageCount()}
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  className="hidden h-8 w-8 p-0 lg:flex"
                  onClick={() => table.setPageIndex(0)}
                  disabled={!table.getCanPreviousPage()}
                >
                  <span className="sr-only">Go to first page</span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                    <path d="m11 17-5-5 5-5"></path>
                    <path d="m18 17-5-5 5-5"></path>
                  </svg>
                </Button>
                <Button
                  variant="outline"
                  className="h-8 w-8 p-0"
                  onClick={() => table.previousPage()}
                  disabled={!table.getCanPreviousPage()}
                >
                  <span className="sr-only">Go to previous page</span>
                  <ChevronDown className="h-4 w-4 rotate-90" />
                </Button>
                <Button
                  variant="outline"
                  className="h-8 w-8 p-0"
                  onClick={() => table.nextPage()}
                  disabled={!table.getCanNextPage()}
                >
                  <span className="sr-only">Go to next page</span>
                  <ChevronDown className="h-4 w-4 -rotate-90" />
                </Button>
                <Button
                  variant="outline"
                  className="hidden h-8 w-8 p-0 lg:flex"
                  onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                  disabled={!table.getCanNextPage()}
                >
                  <span className="sr-only">Go to last page</span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                    <path d="m13 17 5-5-5-5"></path>
                    <path d="m6 17 5-5-5-5"></path>
                  </svg>
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 