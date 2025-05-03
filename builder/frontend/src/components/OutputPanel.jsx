// src/components/OutputPanel.jsx
import React from 'react';
import { useStore } from '../store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from '@/components/ui/scroll-area';
import { Trash2 } from 'lucide-react'; // Icon

const OutputPanel = () => {
  const output = useStore((state) => state.output);
  const clearOutput = useStore((state) => state.clearOutput);
  const isRunning = useStore((state) => state.isRunning);

  const hasContent = output && output !== "Output will appear here..." && output.trim() !== "";

  return (
    <Card className="w-[450px] flex flex-col rounded-none border-l border-t-0 border-b-0 border-r-0 border-border h-full shadow-none">
      {/* Header */}
       <CardHeader className="flex flex-row justify-between items-center p-3 border-b border-border flex-shrink-0 h-16">
            <CardTitle className="text-lg font-semibold">Output</CardTitle> {/* Adjusted size */}
            <Button
                variant="outline"
                size="sm"
                onClick={clearOutput}
                disabled={isRunning || !hasContent}
            >
                <Trash2 className="h-4 w-4 mr-1" /> Clear
            </Button>
       </CardHeader>

      {/* Scrollable Content Area */}
      <CardContent className="flex-grow p-0 overflow-hidden"> {/* Remove padding, add overflow hidden */}
        <ScrollArea className="h-full w-full">
             {/* Add padding inside the scroll area content */}
            <pre className="text-sm text-muted-foreground whitespace-pre-wrap break-words font-mono p-4">
                {hasContent ? output : <span className="text-muted-foreground/70 italic">Output will appear here...</span>}
            </pre>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default OutputPanel;