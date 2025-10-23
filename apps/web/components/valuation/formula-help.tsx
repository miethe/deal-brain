import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Code } from "@/components/ui/code";
import { Copy, HelpCircle } from "lucide-react";
import { toast } from "@/components/ui/toast";

// Function reference data
const FORMULA_FUNCTIONS = [
  {
    name: 'abs',
    description: 'Absolute value',
    syntax: 'abs(x)',
    example: 'abs(-5)  # Returns 5',
    category: 'Mathematical'
  },
  {
    name: 'min',
    description: 'Minimum of two values',
    syntax: 'min(a, b)',
    example: 'min(ram_gb, 32)  # Returns smaller value',
    category: 'Mathematical'
  },
  {
    name: 'max',
    description: 'Maximum of two values',
    syntax: 'max(a, b)',
    example: 'max(price_usd, 100)  # Returns larger value',
    category: 'Mathematical'
  },
  // Add more functions as needed
];

const FORMULA_EXAMPLES = [
  {
    title: 'RAM Pricing Tier',
    formula: 'ram_gb * 3.0 if ram_gb >= 32 else ram_gb * 2.5',
    description: 'Different multipliers for RAM tiers'
  },
  {
    title: 'CPU Performance Scaling',
    formula: 'clamp(cpu.cpu_mark_single / 100 * 5.2, 0, 80)',
    description: 'Scale price by CPU performance with bounds'
  },
  {
    title: 'Condition Discount',
    formula: 'price_usd * 0.85 if condition == "used" else price_usd',
    description: 'Apply discount for used items'
  }
];

export function FormulaHelpDialog() {
  const [activeTab, setActiveTab] = useState('functions');

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      toast({
        title: "Copied to clipboard",
        description: text,
        variant: "default"
      });
    });
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Formula Help">
          <HelpCircle className="h-5 w-5" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Formula Builder Help</DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="functions">Function Reference</TabsTrigger>
            <TabsTrigger value="examples">Example Formulas</TabsTrigger>
          </TabsList>

          <TabsContent value="functions">
            <div className="space-y-4 max-h-[500px] overflow-y-auto">
              {FORMULA_FUNCTIONS.map((func) => (
                <div
                  key={func.name}
                  className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
                >
                  <div className="flex justify-between items-center mb-2">
                    <div>
                      <h3 className="text-lg font-semibold">{func.name}</h3>
                      <p className="text-muted-foreground text-sm">{func.category}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => copyToClipboard(func.syntax)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="text-sm mb-2">{func.description}</p>
                  <Code className="text-xs">{func.example}</Code>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="examples">
            <div className="space-y-4 max-h-[500px] overflow-y-auto">
              {FORMULA_EXAMPLES.map((example) => (
                <div
                  key={example.title}
                  className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
                >
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="text-lg font-semibold">{example.title}</h3>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => copyToClipboard(example.formula)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="text-muted-foreground text-sm mb-2">
                    {example.description}
                  </p>
                  <Code className="text-xs">{example.formula}</Code>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

export default FormulaHelpDialog;