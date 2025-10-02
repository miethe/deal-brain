"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Label } from "../ui/label";
import { Slider } from "../ui/slider";
import { Button } from "../ui/button";
import { Alert, AlertDescription } from "../ui/alert";
import { AlertCircle, Check, Info } from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

interface RuleGroupWeight {
  name: string;
  category: string;
  weight: number;
  color: string;
}

interface WeightConfigProps {
  profileId: number;
  initialWeights: Record<string, number>;
  onSave: (weights: Record<string, number>) => Promise<void>;
  ruleGroups: Array<{ name: string; category: string }>;
}

const CATEGORY_COLORS: Record<string, string> = {
  cpu: "#3b82f6",
  gpu: "#10b981",
  ram: "#8b5cf6",
  storage: "#f59e0b",
  chassis: "#ef4444",
  ports: "#06b6d4",
  os: "#84cc16",
  peripherals: "#ec4899",
  other: "#6b7280",
};

export function WeightConfig({
  profileId,
  initialWeights,
  onSave,
  ruleGroups,
}: WeightConfigProps) {
  const [weights, setWeights] = useState<RuleGroupWeight[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    // Initialize weights from props
    const initializedWeights = ruleGroups.map((group) => ({
      name: group.name,
      category: group.category,
      weight: initialWeights[group.name] || 0,
      color: CATEGORY_COLORS[group.category] || CATEGORY_COLORS.other,
    }));

    // If no weights are set, distribute equally
    if (initializedWeights.every((w) => w.weight === 0)) {
      const equalWeight = 1.0 / initializedWeights.length;
      initializedWeights.forEach((w) => {
        w.weight = Math.round(equalWeight * 100) / 100;
      });
    }

    setWeights(initializedWeights);
  }, [ruleGroups, initialWeights]);

  const totalWeight = weights.reduce((sum, w) => sum + w.weight, 0);
  const isValid = Math.abs(totalWeight - 1.0) < 0.01;

  const handleWeightChange = (index: number, newValue: number) => {
    const newWeights = [...weights];
    newWeights[index].weight = newValue / 100; // Slider value is 0-100, convert to 0-1
    setWeights(newWeights);
    setError(null);
    setSuccess(false);
  };

  const handleNormalize = () => {
    // Normalize weights to sum to 1.0
    const total = weights.reduce((sum, w) => sum + w.weight, 0);
    if (total === 0) return;

    const normalized = weights.map((w) => ({
      ...w,
      weight: Math.round((w.weight / total) * 100) / 100,
    }));

    // Adjust the first weight to account for rounding errors
    const newTotal = normalized.reduce((sum, w) => sum + w.weight, 0);
    if (Math.abs(newTotal - 1.0) > 0.001) {
      normalized[0].weight = Math.round((normalized[0].weight + (1.0 - newTotal)) * 100) / 100;
    }

    setWeights(normalized);
    setError(null);
  };

  const handleReset = () => {
    const equalWeight = Math.round((1.0 / weights.length) * 100) / 100;
    const resetWeights = weights.map((w, index) => ({
      ...w,
      weight: index === 0 ? 1.0 - equalWeight * (weights.length - 1) : equalWeight,
    }));
    setWeights(resetWeights);
    setError(null);
    setSuccess(false);
  };

  const handleSave = async () => {
    if (!isValid) {
      setError("Weights must sum to 1.0 before saving");
      return;
    }

    setIsSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const weightsObject = weights.reduce(
        (acc, w) => {
          acc[w.name] = w.weight;
          return acc;
        },
        {} as Record<string, number>
      );

      await onSave(weightsObject);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save weights");
    } finally {
      setIsSaving(false);
    }
  };

  const chartData = weights
    .filter((w) => w.weight > 0)
    .map((w) => ({
      name: w.category,
      value: Math.round(w.weight * 100),
      color: w.color,
    }));

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Rule Group Weights</CardTitle>
          <CardDescription>
            Configure how much each rule group contributes to the overall valuation.
            Weights must sum to 1.0 (100%).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Weight Status Alert */}
          {!isValid && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Weights currently sum to {totalWeight.toFixed(3)}. They must sum to 1.0.
                <Button
                  variant="link"
                  size="sm"
                  onClick={handleNormalize}
                  className="ml-2 h-auto p-0"
                >
                  Normalize Now
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {isValid && !success && (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Weights are balanced ({totalWeight.toFixed(3)}). Ready to save.
              </AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert className="border-green-500 bg-green-50">
              <Check className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-600">
                Weights saved successfully!
              </AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Weight Sliders */}
          <div className="space-y-4">
            {weights.map((weight, index) => (
              <div key={weight.name} className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor={`weight-${index}`} className="flex items-center gap-2">
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: weight.color }}
                    />
                    <span className="font-medium">{weight.category}</span>
                    <span className="text-sm text-muted-foreground">({weight.name})</span>
                  </Label>
                  <span className="text-sm font-mono">
                    {(weight.weight * 100).toFixed(1)}%
                  </span>
                </div>
                <Slider
                  id={`weight-${index}`}
                  value={[weight.weight * 100]}
                  onValueChange={(values) => handleWeightChange(index, values[0])}
                  min={0}
                  max={100}
                  step={1}
                  className="flex-1"
                />
              </div>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <Button onClick={handleSave} disabled={!isValid || isSaving}>
              {isSaving ? "Saving..." : "Save Weights"}
            </Button>
            <Button variant="outline" onClick={handleNormalize} disabled={isValid}>
              Normalize
            </Button>
            <Button variant="outline" onClick={handleReset}>
              Reset to Equal
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Weight Distribution Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Weight Distribution</CardTitle>
          <CardDescription>Visual representation of rule group weights</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Weight Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Total Weight:</span>
              <span className={`ml-2 font-mono font-medium ${isValid ? "text-green-600" : "text-red-600"}`}>
                {totalWeight.toFixed(3)}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Rule Groups:</span>
              <span className="ml-2 font-medium">{weights.length}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Non-zero Weights:</span>
              <span className="ml-2 font-medium">
                {weights.filter((w) => w.weight > 0).length}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Average Weight:</span>
              <span className="ml-2 font-mono">
                {(totalWeight / weights.length).toFixed(3)}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
