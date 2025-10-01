"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Upload } from "lucide-react";
import { useRouter } from "next/navigation";

import { apiFetch } from "../../lib/utils";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { GlobalFieldsTable } from "./global-fields-table";
import { GlobalFieldsDataTab } from "./global-fields-data-tab";

interface EntityRecord {
  entity: string;
  label: string;
  primary_key: string;
  supports_custom_fields: boolean;
}

interface EntityListResponse {
  entities: EntityRecord[];
}

export function GlobalFieldsWorkspace() {
  const router = useRouter();
  const { data, isLoading } = useQuery<EntityListResponse>({
    queryKey: ["fields-data", "entities"],
    queryFn: () => apiFetch<EntityListResponse>("/v1/fields-data/entities"),
  });

  const entities = useMemo(() => data?.entities ?? [], [data]);
  const defaultEntity = entities[0]?.entity ?? "listing";
  const [selectedEntity, setSelectedEntity] = useState<string>(defaultEntity);
  const [activeTab, setActiveTab] = useState<"fields" | "data">("fields");

  useEffect(() => {
    if (!entities.length) return;
    const hasSelection = entities.some((item) => item.entity === selectedEntity);
    if (!hasSelection) {
      setSelectedEntity(entities[0].entity);
    }
  }, [entities, selectedEntity]);

  const activeLabel = useMemo(() => {
    return entities.find((item) => item.entity === selectedEntity)?.label ?? selectedEntity;
  }, [entities, selectedEntity]);

  if (isLoading) {
    return <div className="rounded-lg border p-6 text-sm text-muted-foreground">Loading global fields…</div>;
  }

  return (
    <div className="grid w-full gap-6 lg:grid-cols-[240px_1fr]">
      <aside className="space-y-4">
        <div>
          <h2 className="text-xs font-semibold uppercase text-muted-foreground">Entities</h2>
          <nav className="mt-2 space-y-1">
            {entities.map((entity) => (
              <Button
                key={entity.entity}
                variant={entity.entity === selectedEntity ? "secondary" : "ghost"}
                className="w-full justify-start"
                onClick={() => setSelectedEntity(entity.entity)}
              >
                {entity.label}
              </Button>
            ))}
          </nav>
        </div>
        <Card className="p-3 text-xs text-muted-foreground">
          Manage core definitions and data entries for each catalog entity. Custom fields automatically sync to importer
          mapping and manual entry forms.
        </Card>
      </aside>
      <section className="min-w-0 space-y-6">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold tracking-tight">{activeLabel}</h1>
          <p className="text-sm text-muted-foreground">
            Configure metadata and data entries for the selected entity.
          </p>
        </div>
        <div className="flex items-center justify-between gap-4">
          <div className="inline-flex rounded-md border bg-muted p-1">
            <Button
              variant={activeTab === "fields" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("fields")}
            >
              Fields
            </Button>
            <Button
              variant={activeTab === "data" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("data")}
            >
              Data
            </Button>
          </div>
          {activeTab === "data" && (
            <Button
              variant="default"
              onClick={() => {
                router.push(`/import?entity=${selectedEntity}&return=/global-fields`);
              }}
            >
              <Upload className="mr-2 h-4 w-4" />
              Import Data
            </Button>
          )}
        </div>
        <div className="mt-6">
          {activeTab === "fields" ? (
            <GlobalFieldsTable entity={selectedEntity} hideEntityPicker />
          ) : (
            <GlobalFieldsDataTab entity={selectedEntity} />
          )}
        </div>
      </section>
    </div>
  );
}
