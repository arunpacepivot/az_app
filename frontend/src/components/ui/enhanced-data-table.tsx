import React, { useState, useMemo } from 'react'
import { DataTable } from './data-table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs'
import { ColumnDef } from '@tanstack/react-table'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './card'

interface EnhancedDataTableProps {
  data: Record<string, Array<Record<string, any>>>
  title?: string
  description?: string
  onDownload?: () => void
}

export function EnhancedDataTable({
  data,
  title = "Excel Data Preview",
  description = "Preview and analyze the optimized data before download",
  onDownload
}: EnhancedDataTableProps) {
  // Get all available sheets (tabs) from the data
  const sheets = Object.keys(data)
  
  // Set active sheet to the first one by default
  const [activeSheet, setActiveSheet] = useState<string>(() => {
    return sheets.length > 0 ? sheets[0] : ''
  })

  // Generate columns based on the first row of data in the active sheet
  const columns = useMemo(() => {
    if (!activeSheet || !data[activeSheet] || data[activeSheet].length === 0) {
      return []
    }

    const firstRow = data[activeSheet][0]
    return Object.keys(firstRow).map((key) => ({
      accessorKey: key,
      header: key,
      cell: ({ row }) => {
        const value = row.getValue(key)
        // Format cell based on value type
        if (typeof value === 'number') {
          // Format numbers with 2 decimal places
          return Number.isInteger(value) ? value : value.toFixed(2)
        }
        return value
      },
    })) as ColumnDef<any>[]
  }, [activeSheet, data])

  // Get the current sheet data
  const sheetData = useMemo(() => {
    return activeSheet && data[activeSheet] ? data[activeSheet] : []
  }, [activeSheet, data])

  // Get row count for the active sheet
  const rowCount = sheetData.length

  return (
    <Card className="w-full mt-6 border border-gray-700 shadow-xl bg-gray-900/60 backdrop-blur-sm">
      <CardHeader className="border-b border-gray-700/50 pb-3">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <CardTitle className="text-xl font-bold text-yellow-400">
              {title}
            </CardTitle>
            {description && (
              <CardDescription className="text-gray-300 mt-1">
                {description}
              </CardDescription>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <Tabs defaultValue={activeSheet} onValueChange={setActiveSheet} className="w-full">
          <div className="border-b border-gray-700">
            <div className="overflow-x-auto">
              <TabsList className="h-12 px-2 bg-gray-800/50">
                {sheets.map((sheet) => (
                  <TabsTrigger
                    key={sheet}
                    value={sheet}
                    className="data-[state=active]:bg-gray-700 data-[state=active]:text-yellow-400 rounded-sm px-3 py-1.5 text-sm font-medium"
                  >
                    {sheet}
                  </TabsTrigger>
                ))}
              </TabsList>
            </div>
          </div>
          
          {sheets.map((sheet) => (
            <TabsContent key={sheet} value={sheet} className="p-0 border-0">
              <div className="p-4">
                <div className="text-sm text-gray-400 mb-2">
                  {rowCount} row{rowCount !== 1 ? 's' : ''}
                </div>
                <DataTable
                  columns={columns}
                  data={sheetData}
                  enableSorting={true}
                  enableFiltering={true}
                  enableColumnVisibility={true}
                  enablePagination={true}
                  onDownload={onDownload}
                />
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </CardContent>
    </Card>
  )
} 