/**
 * Utility functions for formula manipulation and validation
 */

export interface Operation {
  label: string;
  value: string;
  type: "operator" | "function" | "group" | "logical";
  description?: string;
  insertCursorOffset?: number; // Offset from end of inserted text for cursor positioning
}

export const MATH_OPERATIONS: Operation[] = [
  { label: "+", value: " + ", type: "operator", description: "Addition" },
  { label: "-", value: " - ", type: "operator", description: "Subtraction" },
  { label: "×", value: " * ", type: "operator", description: "Multiplication" },
  { label: "÷", value: " / ", type: "operator", description: "Division" },
  { label: "%", value: " % ", type: "operator", description: "Modulo" },
  { label: "^", value: " ** ", type: "operator", description: "Exponentiation" },
];

export const COMPARISON_OPERATIONS: Operation[] = [
  { label: "==", value: " == ", type: "logical", description: "Equal to" },
  { label: "!=", value: " != ", type: "logical", description: "Not equal to" },
  { label: ">", value: " > ", type: "logical", description: "Greater than" },
  { label: ">=", value: " >= ", type: "logical", description: "Greater than or equal" },
  { label: "<", value: " < ", type: "logical", description: "Less than" },
  { label: "<=", value: " <= ", type: "logical", description: "Less than or equal" },
];

export const LOGICAL_OPERATIONS: Operation[] = [
  { label: "and", value: " and ", type: "logical", description: "Logical AND" },
  { label: "or", value: " or ", type: "logical", description: "Logical OR" },
  { label: "not", value: "not ", type: "logical", description: "Logical NOT" },
];

export const FUNCTION_OPERATIONS: Operation[] = [
  { label: "min()", value: "min()", type: "function", description: "Minimum value", insertCursorOffset: -1 },
  { label: "max()", value: "max()", type: "function", description: "Maximum value", insertCursorOffset: -1 },
  { label: "round()", value: "round()", type: "function", description: "Round to nearest integer", insertCursorOffset: -1 },
  { label: "abs()", value: "abs()", type: "function", description: "Absolute value", insertCursorOffset: -1 },
  { label: "sqrt()", value: "sqrt()", type: "function", description: "Square root", insertCursorOffset: -1 },
  { label: "pow()", value: "pow(, )", type: "function", description: "Power", insertCursorOffset: -4 },
];

export const GROUP_OPERATIONS: Operation[] = [
  { label: "()", value: "()", type: "group", description: "Parentheses", insertCursorOffset: -1 },
];

export const ALL_OPERATIONS: Operation[] = [
  ...MATH_OPERATIONS,
  ...COMPARISON_OPERATIONS,
  ...LOGICAL_OPERATIONS,
  ...FUNCTION_OPERATIONS,
  ...GROUP_OPERATIONS,
];

export interface FormulaTemplate {
  name: string;
  formula: string;
  description: string;
  category: string;
}

export const FORMULA_TEMPLATES: FormulaTemplate[] = [
  {
    name: "CPU Performance Value",
    formula: "cpu.cpu_mark_single * 0.05",
    description: "Value based on single-thread CPU performance",
    category: "CPU",
  },
  {
    name: "RAM Value",
    formula: "ram_gb * 2.5",
    description: "Simple per-GB RAM pricing",
    category: "RAM",
  },
  {
    name: "Storage Value",
    formula: "primary_storage_gb * 0.1 if primary_storage_type == 'ssd' else primary_storage_gb * 0.05",
    description: "Storage value with SSD premium",
    category: "Storage",
  },
  {
    name: "Minimum Value Enforcement",
    formula: "max(ram_gb * 2.5, 50)",
    description: "Ensure minimum value of $50",
    category: "General",
  },
  {
    name: "Tiered RAM Pricing",
    formula: "ram_gb * 3.0 if ram_gb >= 32 else ram_gb * 2.5",
    description: "Higher per-GB rate for 32GB+",
    category: "RAM",
  },
  {
    name: "Multi-Thread Performance",
    formula: "cpu.cpu_mark_multi / 1000 * 5.0",
    description: "Value based on multi-thread benchmark",
    category: "CPU",
  },
  {
    name: "Combined Storage Value",
    formula: "primary_storage_gb * 0.1 + secondary_storage_gb * 0.08",
    description: "Value both primary and secondary storage",
    category: "Storage",
  },
  {
    name: "Performance per Dollar",
    formula: "round(cpu.cpu_mark_single / price_usd * 10, 2)",
    description: "Calculate performance efficiency score",
    category: "Performance",
  },
];

/**
 * Insert text at cursor position in a text input/textarea
 */
export function insertAtCursor(
  currentValue: string,
  textToInsert: string,
  cursorPosition: number,
  cursorOffset: number = 0
): { newValue: string; newCursorPosition: number } {
  const before = currentValue.slice(0, cursorPosition);
  const after = currentValue.slice(cursorPosition);
  const newValue = before + textToInsert + after;

  // Calculate new cursor position
  // If cursorOffset is negative, position before the end (e.g., -1 puts cursor before last char)
  const newCursorPosition = cursorOffset < 0
    ? cursorPosition + textToInsert.length + cursorOffset
    : cursorPosition + textToInsert.length + cursorOffset;

  return { newValue, newCursorPosition };
}

/**
 * Get cursor position from a text input/textarea element
 */
export function getCursorPosition(element: HTMLTextAreaElement | HTMLInputElement | null): number {
  if (!element) return 0;
  return element.selectionStart || 0;
}

/**
 * Set cursor position in a text input/textarea element
 */
export function setCursorPosition(
  element: HTMLTextAreaElement | HTMLInputElement | null,
  position: number
): void {
  if (!element) return;

  // Use setTimeout to ensure DOM updates have completed
  setTimeout(() => {
    element.selectionStart = position;
    element.selectionEnd = position;
    element.focus();
  }, 0);
}

/**
 * Extract field references from a formula string
 * Looks for identifiers that could be field names
 */
export function extractFieldReferences(formula: string): string[] {
  // Match identifiers (field names) - alphanumeric + underscore + dots for nested fields
  const fieldPattern = /[a-zA-Z_][a-zA-Z0-9_.]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?/g;
  const matches = formula.match(fieldPattern) || [];

  // Filter out Python keywords and common function names
  const pythonKeywords = new Set([
    "if", "else", "elif", "for", "while", "in", "is", "not", "and", "or",
    "True", "False", "None", "min", "max", "round", "abs", "sqrt", "pow",
  ]);

  const fields = matches.filter(match => !pythonKeywords.has(match));

  // Return unique fields
  return Array.from(new Set(fields));
}

/**
 * Highlight syntax in a formula string
 * Returns array of tokens with type information for styling
 */
export interface SyntaxToken {
  text: string;
  type: "keyword" | "operator" | "function" | "number" | "field" | "string" | "comment" | "default";
}

export function highlightSyntax(formula: string): SyntaxToken[] {
  const tokens: SyntaxToken[] = [];

  const keywords = /\b(if|else|elif|for|while|in|is|not|and|or|True|False|None)\b/g;
  const operators = /[+\-*/%<>=!]+/g;
  const functions = /\b(min|max|round|abs|sqrt|pow)\s*\(/g;
  const numbers = /\b\d+\.?\d*\b/g;
  const strings = /"[^"]*"|'[^']*'/g;

  // Simple tokenization - not perfect but good enough for basic highlighting
  // In production, consider using a proper tokenizer/parser

  let lastIndex = 0;
  const matches: Array<{ index: number; length: number; type: SyntaxToken["type"]; text: string }> = [];

  // Find all matches
  let match: RegExpExecArray | null;

  while ((match = keywords.exec(formula)) !== null) {
    matches.push({ index: match.index, length: match[0].length, type: "keyword", text: match[0] });
  }

  while ((match = functions.exec(formula)) !== null) {
    matches.push({ index: match.index, length: match[0].length - 1, type: "function", text: match[0].slice(0, -1) });
  }

  while ((match = numbers.exec(formula)) !== null) {
    matches.push({ index: match.index, length: match[0].length, type: "number", text: match[0] });
  }

  while ((match = strings.exec(formula)) !== null) {
    matches.push({ index: match.index, length: match[0].length, type: "string", text: match[0] });
  }

  // Sort by index
  matches.sort((a, b) => a.index - b.index);

  // Build tokens
  for (const m of matches) {
    if (m.index > lastIndex) {
      // Add text before this match
      tokens.push({ text: formula.slice(lastIndex, m.index), type: "default" });
    }
    tokens.push({ text: m.text, type: m.type });
    lastIndex = m.index + m.length;
  }

  // Add remaining text
  if (lastIndex < formula.length) {
    tokens.push({ text: formula.slice(lastIndex), type: "default" });
  }

  return tokens;
}

/**
 * Format a formula for display (pretty print)
 */
export function formatFormula(formula: string): string {
  // Basic formatting: ensure spaces around operators
  return formula
    .replace(/([+\-*/%<>=!])(?!\s)/g, "$1 ")
    .replace(/(?<!\s)([+\-*/%<>=!])/g, " $1")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Validate basic formula syntax (client-side check before API call)
 */
export function validateFormulaBasic(formula: string): { valid: boolean; error?: string } {
  if (!formula || formula.trim().length === 0) {
    return { valid: false, error: "Formula cannot be empty" };
  }

  // Check for balanced parentheses
  let depth = 0;
  for (const char of formula) {
    if (char === "(") depth++;
    if (char === ")") depth--;
    if (depth < 0) {
      return { valid: false, error: "Unbalanced parentheses: too many closing parentheses" };
    }
  }
  if (depth > 0) {
    return { valid: false, error: "Unbalanced parentheses: missing closing parentheses" };
  }

  // Check for empty parentheses
  if (/\(\s*\)/.test(formula)) {
    return { valid: false, error: "Empty parentheses found" };
  }

  // Check for consecutive operators (but allow negative numbers)
  if (/[+\-*/%][+*/%]/.test(formula)) {
    return { valid: false, error: "Consecutive operators found" };
  }

  return { valid: true };
}
