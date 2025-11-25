---
title: "URL Import Enhancement: Partial Data Extraction & Manual Field Population"
description: "Enable partial data extraction from URLs with user-driven manual field population, eliminating all-or-nothing import failures and supporting real-time UI updates"
audience: [developers, ai-agents, pm]
tags:
  - import
  - ingestion
  - partial-data
  - manual-population
  - real-time-updates
  - feature-enhancement
created: 2025-11-07
updated: 2025-11-07
category: product-planning
status: draft
related:
  - /docs/project_plans/requests/completed/listings-enhancements-v3.md
---

# URL Import Enhancement: Partial Data Extraction & Manual Field Population

## Executive Summary

The current URL import system uses an all-or-nothing approach: if any critical field (price, title) fails to extract, the entire import fails and the user loses all extracted data (images, specs, descriptions). This results in ~30% import success rate for Amazon and other sources.

This PRD enables **partial data extraction** and **real-time manual field population**, allowing users to successfully import listings with partial data and immediately fill gaps via a modal UI. This increases import success rates to 80%+ while maintaining data quality through validation.

---

## Problem Statement

### Current Behavior

The existing import pipeline enforces strict schema validation:

1. **All-or-Nothing Extraction**: Adapters (eBay API, JSON-LD, Amazon scraper) must extract BOTH title AND price
2. **Required Schema Fields**: `NormalizedListingSchema` marks `title` and `price` as required fields
3. **Early Failure**: If price extraction fails for any reason, the entire import is rejected
4. **Data Loss**: User loses valuable extracted data (title, images, CPU specs, description)
5. **No Recovery Path**: No UI to manually fill missing fields after import

### Current Adapter Requirements

In `BaseAdapter._validate_response()`:
```python
required_fields = ["title", "price"]
missing = [f for f in required_fields if f not in data or not data[f]]
if missing:
    raise AdapterException(
        AdapterError.INVALID_SCHEMA,
        f"Missing required fields: {', '.join(missing)}",
    )
```

### User Pain Points

- **Amazon Imports**: Price extraction fails 60-70% of the time due to dynamic pricing, missing price elements, or JavaScript rendering
- **Valuable Data Lost**: Title, images, CPU model, RAM, storage specs are extracted but discarded
- **Manual Workaround**: Users manually enter listings instead of importing, duplicating effort
- **Low Success Rate**: ~30% of attempted imports succeed on first try, requiring manual import as fallback
- **No Real-Time Feedback**: Users must refresh page to see import results
- **Data Entry Overhead**: Even partial imports require manual price entry without UI support

### Business Impact

- **Import Adoption**: Low confidence in import feature drives users to manual entry
- **Time Waste**: Users spend 5-10 minutes per listing on manual entry vs. 30 seconds on URL import
- **Marketplace Expansion**: Amazon, Etsy, and other non-native marketplaces have low import success
- **Competitive Disadvantage**: Competing tools support partial imports with manual population
- **Support Burden**: User requests for import failures consume support resources

---

## Goals & Success Metrics

### Primary Goals

1. **Enable Partial Data Extraction**: Accept imports with at least title OR (CPU model + manufacturer), not both required fields
2. **Support Real-Time Manual Population**: UI modal for immediately filling missing fields after import
3. **Improve Import Success Rate**: Increase from ~30% to 80%+ for all marketplaces
4. **Real-Time UI Feedback**: Update listings grid/table without page refresh when imports complete
5. **Maintain Data Quality**: Validate manually entered fields before final submission

### Success Metrics

| Metric | Current | Target | Rationale |
|--------|---------|--------|-----------|
| **Import Success Rate** | ~30% | 80%+ | Measure partial + full imports |
| **Partial Import Rate** | 0% | 15-25% | Expected % of partial imports |
| **Manual Completion Rate** | N/A | 70%+ | % of users completing modal |
| **Time to Import** | 5-10 min | 30-60 sec | Faster than manual entry |
| **Amazon Success Rate** | ~20% | 70%+ | Biggest pain point improvement |
| **Data Quality Score** | ~85% | 90%+ | Validation prevents bad data |
| **UI Page Refresh Needed** | 100% | 0% | Real-time updates |

---

## User Stories

### Story 1: Partial Import with Manual Completion
**As a** user importing from Amazon
**I want** to import a listing even if price extraction fails
**So that** I can quickly add the price manually instead of losing all data

**Acceptance Criteria:**
- Import succeeds with title, images, and specs but no price
- Modal auto-opens showing extracted data (read-only) and price field (editable)
- User enters price: $299.99
- User clicks "Save" and listing appears in dashboard
- Listing shows full data with quality indicator "partial"

**Example Flow:**
```
URL Submission
  ↓
Adapter extraction → Title: "Dell OptiPlex 7090", Images: [3], Specs: found, Price: null
  ↓
Import succeeds with quality="partial"
  ↓
Modal opens: "Fill 1 missing field to complete listing"
  ↓
User enters price: $299.99
  ↓
Listing saved and appears in grid with "price manually entered" badge
```

### Story 2: Real-Time Import Status
**As a** user importing multiple URLs
**I want** to see import results in real-time without refreshing
**So that** I can immediately view and act on imported listings

**Acceptance Criteria:**
- User uploads 5 URLs
- Page shows progress indicator (2/5 completed)
- Each URL completion updates grid in real-time
- Toast notification appears for each successful import
- "View" button in toast opens modal with extracted data

**Example Flow:**
```
Bulk Upload (5 URLs)
  ↓
Progress shown: "Processing 5 imports..."
  ↓
Import 1 completes → Grid updates, toast: "Dell OptiPlex imported"
  ↓
Import 2 completes (partial) → Toast: "HP Mini PC (price needed)"
  ↓
User clicks "Complete" in toast → Modal opens for manual entry
  ↓
Import 3, 4, 5 complete → Grid shows all results
```

### Story 3: Bulk Manual Population
**As a** user with 3 partial imports
**I want** to complete them all at once with a summary view
**So that** I don't need to open 3 separate modals

**Acceptance Criteria:**
- Partial imports are grouped in UI
- "Complete All Partial" button shows summary of missing fields
- Modal shows all 3 listings side-by-side
- User fills all prices and submits once
- All 3 listings save and update grid

**Future Enhancement** (Phase 4+, not in initial scope)

### Story 4: Quality Indicators
**As a** user managing imported listings
**I want** to see which fields were extracted vs. manually entered
**So that** I can trust data quality and know what needs review

**Acceptance Criteria:**
- Listing shows badges: "Price manually entered", "Extracted from Amazon", "Verified CPU"
- Modal highlights field source: Green (extracted), Yellow (manual), Red (needs review)
- Dashboard filter: "Show partial imports", "Show manual entries"
- Admin dashboard shows data quality trends

**Future Enhancement** (Phase 4+, not in initial scope)

---

## Technical Requirements

### Phase 1: Backend - Partial Extraction Support

**Duration**: 2-3 days
**Deliverable**: Support partial imports; allow null price in database

#### 1.1 Schema Changes

**File**: `packages/core/dealbrain_core/schemas/ingestion.py`

Update `NormalizedListingSchema`:
- Make `price` optional: `price: Decimal | None = Field(default=None, ...)`
- Add minimum field requirement validation
- Add `quality` field: `quality: str = Field(default="full", pattern=r"^(full|partial)$")`
- Add `extraction_metadata` for tracking which fields were extracted

```python
class NormalizedListingSchema(DealBrainModel):
    title: str | None = Field(default=None, ...)  # Optional for CPU-model-only imports
    price: Decimal | None = Field(default=None, description="Optional - may be filled manually")
    quality: str = Field(default="full", pattern=r"^(full|partial)$")
    extraction_metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Map of field -> source (e.g., {'price': 'manual', 'title': 'extracted'})"
    )

    @field_validator("price", mode="before")
    @classmethod
    def validate_price_optional(cls, value: Any) -> Decimal | None:
        """Allow null prices for partial imports."""
        if value is None or value == "":
            return None
        # Validate positive if present
        if isinstance(value, (int, float)):
            if value <= 0:
                raise ValueError("Price must be positive if provided")
            return Decimal(str(value))
        return value

    def validate_minimum_fields(self) -> None:
        """Ensure at least one required field group is present."""
        has_title = self.title and self.title.strip()
        has_cpu_model = self.cpu_model and self.cpu_model.strip()
        has_manufacturer = self.manufacturer and self.manufacturer.strip()

        if not (has_title or (has_cpu_model and has_manufacturer)):
            raise ValueError(
                "Listing requires either title OR (cpu_model + manufacturer) to proceed"
            )
```

#### 1.2 Adapter Updates

**Files**:
- `apps/api/dealbrain_api/adapters/base.py`
- `apps/api/dealbrain_api/adapters/jsonld.py`
- `apps/api/dealbrain_api/adapters/ebay.py`

Update `BaseAdapter._validate_response()`:
```python
def _validate_response(self, data: dict[str, Any]) -> None:
    """Validate that minimum fields are present for import."""
    # Track which fields were extracted
    extracted_fields = {k: "extracted" for k, v in data.items() if v}

    # Minimum requirement: title OR (cpu_model + manufacturer)
    has_title = data.get("title", "").strip()
    has_cpu_and_mfg = data.get("cpu_model", "").strip() and data.get("manufacturer", "").strip()

    if not (has_title or has_cpu_and_mfg):
        raise AdapterException(
            AdapterError.INVALID_SCHEMA,
            "Listing requires either title OR (cpu_model + manufacturer) to import",
            metadata={"extracted_fields": list(extracted_fields.keys())}
        )

    # Price is now optional - don't require it
    # Log warning if missing but continue
    if not data.get("price"):
        logger.warning(f"[{self.name}] No price extracted - import will be partial")
```

#### 1.3 Database Schema

**File**: `apps/api/alembic/versions/0021_partial_import_support.py`

Create migration:
```python
def upgrade():
    # Make price nullable
    op.alter_column('listings', 'price_usd',
        existing_type=sa.DECIMAL(10, 2),
        nullable=True)

    # Add quality column to ImportSession
    op.add_column('import_sessions',
        sa.Column('quality', sa.String(20), nullable=False, server_default='full'))

    # Add extraction_metadata JSON column
    op.add_column('import_sessions',
        sa.Column('extraction_metadata', sa.JSON(), nullable=False, server_default='{}'))

def downgrade():
    op.drop_column('import_sessions', 'extraction_metadata')
    op.drop_column('import_sessions', 'quality')
    op.alter_column('listings', 'price_usd',
        existing_type=sa.DECIMAL(10, 2),
        nullable=False)
```

#### 1.4 Ingestion Service

**File**: `apps/api/dealbrain_api/services/imports.py`

Update import pipeline:
```python
async def process_import(
    self,
    listing_data: NormalizedListingSchema,
    source_url: str,
    user_id: str,
    quality: str = "full"
) -> Listing:
    """
    Process normalized listing data into database.

    Args:
        listing_data: Normalized schema (may have null price)
        source_url: Original URL imported from
        user_id: Clerk user ID
        quality: "full" or "partial"

    Returns:
        Created Listing record
    """
    # Validate minimum fields
    listing_data.validate_minimum_fields()

    # Create listing with nullable price
    listing = Listing(
        title=listing_data.title,
        price_usd=listing_data.price,  # May be None
        manufacturer=listing_data.manufacturer,
        cpu_model=listing_data.cpu_model,
        marketplace=listing_data.marketplace,
        # ... other fields ...
        quality=quality,
        extraction_metadata=listing_data.extraction_metadata or {},
    )

    # If price is null, don't calculate metrics yet
    if listing.price_usd:
        await self._apply_valuation_rules(listing)

    await session.add(listing)
    await session.commit()
    return listing
```

#### 1.5 Error Handling

Update error messages to distinguish between:
- **Critical Failure**: No title AND no CPU model + manufacturer → fail import
- **Partial Import**: Has minimum fields but missing price/specs → succeed with quality="partial"
- **Network Error**: Temporary failure → retry
- **Parsing Error**: Adapter cannot parse response → fail

### Phase 2: Backend - Real-Time Status Updates

**Duration**: 1-2 days
**Deliverable**: Import status polling endpoint, WebSocket support (optional)

#### 2.1 Import Status Endpoint

**File**: `apps/api/dealbrain_api/api/ingestion.py`

Add new endpoint:
```python
@router.get("/api/v1/ingest/bulk/{bulk_job_id}/status")
async def get_bulk_import_status(
    bulk_job_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(session_dependency),
) -> BulkIngestionStatusResponse:
    """
    Poll import job status with pagination.

    Returns:
        - Overall job status
        - Per-URL status with pagination
        - Progress counts (queued, running, complete, partial, failed)
    """
    # Fetch BulkImportJob from database
    # Return status with per-row details
```

#### 2.2 Job Status Tracking

**File**: `apps/api/dealbrain_api/models/core.py`

Update `ImportSession` model:
```python
class ImportSession(Base):
    __tablename__ = "import_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    bulk_job_id: Mapped[str | None] = mapped_column(String(36), index=True)
    url: Mapped[str] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(20))  # queued|running|complete|partial|failed
    quality: Mapped[str] = mapped_column(String(20), default="full")
    listing_id: Mapped[int | None] = mapped_column(ForeignKey("listings.id"), nullable=True)
    extraction_metadata: Mapped[dict] = mapped_column(JSON(), default=dict)
    error_details: Mapped[dict | None] = mapped_column(JSON(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

#### 2.3 Task Updates

**File**: `apps/api/dealbrain_api/tasks/ingestion.py`

Update task to track status:
```python
@app.task(bind=True, name="ingest_url")
async def ingest_url_task(self, job_id: str, url: str, user_id: str):
    """Ingest single URL with status tracking."""
    session = ImportSession(job_id=job_id, url=url, status="running")

    try:
        # Extract data
        normalized = await ingestion_service.extract(url)

        # Determine quality
        quality = "partial" if normalized.price is None else "full"

        # Create listing
        listing = await listings_service.create(normalized, quality=quality)

        # Update status
        session.status = "complete" if quality == "full" else "partial"
        session.listing_id = listing.id
        session.quality = quality
        session.completed_at = utcnow()

    except Exception as e:
        session.status = "failed"
        session.error_details = {"error": str(e)}
        session.completed_at = utcnow()

    await db.commit()
```

#### 2.4 WebSocket Support (Optional)

For real-time updates without polling:
```python
@router.websocket("/ws/ingest/bulk/{bulk_job_id}")
async def websocket_bulk_status(
    websocket: WebSocket,
    bulk_job_id: str,
):
    """WebSocket for real-time import status updates."""
    # On connection, send current status
    # Listen for status changes in Redis
    # Push updates to client
```

### Phase 3: Frontend - Manual Population Modal

**Duration**: 2-3 days
**Deliverable**: Modal UI for manual field entry after partial import

#### 3.1 Modal Component

**File**: `apps/web/components/imports/PartialImportModal.tsx`

```typescript
interface PartialImportModalProps {
  importSession: ImportSession;
  extractedData: NormalizedListingSchema;
  onComplete: (completeData: NormalizedListingSchema) => void;
  onCancel: () => void;
}

export function PartialImportModal({
  importSession,
  extractedData,
  onComplete,
}: PartialImportModalProps) {
  const [formData, setFormData] = useState(extractedData);
  const [errors, setErrors] = useState<Record<string, string>>({});

  return (
    <Dialog open={true} onOpenChange={onCancel}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Complete Import</DialogTitle>
          <DialogDescription>
            We extracted most data, but need your help with {missingFields.length} fields
          </DialogDescription>
        </DialogHeader>

        {/* Extracted Data (Read-Only) */}
        <div className="space-y-4">
          <h3 className="font-semibold">Extracted Data</h3>
          <ExtractedFieldsSection data={extractedData} />

          {/* Missing Fields (Editable) */}
          <h3 className="font-semibold">Complete These Fields</h3>
          <MissingFieldsForm
            data={formData}
            missingFields={missingFields}
            errors={errors}
            onChange={setFormData}
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>Skip</Button>
          <Button onClick={() => validateAndSubmit()}>Save Listing</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

#### 3.2 Extracted Fields Display

```typescript
function ExtractedFieldsSection({ data }: { data: NormalizedListingSchema }) {
  const fields = [
    { label: "Title", value: data.title, icon: Check },
    { label: "Images", value: `${data.images?.length || 0} images`, icon: Check },
    { label: "CPU Model", value: data.cpu_model, icon: Check },
    { label: "RAM", value: data.ram_gb ? `${data.ram_gb}GB` : null, icon: Check },
    { label: "Storage", value: data.storage_gb ? `${data.storage_gb}GB` : null, icon: Check },
  ];

  return (
    <div className="space-y-2">
      {fields.map(field => field.value && (
        <div key={field.label} className="flex items-center gap-2">
          <field.icon className="w-4 h-4 text-green-600" />
          <span className="text-sm">{field.label}: {field.value}</span>
        </div>
      ))}
    </div>
  );
}
```

#### 3.3 Missing Fields Form

```typescript
function MissingFieldsForm({
  data,
  missingFields,
  errors,
  onChange,
}: {
  data: NormalizedListingSchema;
  missingFields: string[];
  errors: Record<string, string>;
  onChange: (data: NormalizedListingSchema) => void;
}) {
  return (
    <Form>
      {missingFields.includes("price") && (
        <div className="border-l-4 border-yellow-400 pl-4">
          <Label htmlFor="price">Price (Required)</Label>
          <Input
            id="price"
            type="number"
            step="0.01"
            min="0"
            placeholder="0.00"
            value={data.price || ""}
            onChange={(e) => onChange({ ...data, price: Decimal(e.target.value) })}
            className={errors.price ? "border-red-500" : ""}
          />
          {errors.price && <p className="text-xs text-red-500">{errors.price}</p>}
        </div>
      )}

      {missingFields.includes("manufacturer") && (
        <div>
          <Label htmlFor="manufacturer">Manufacturer (Required)</Label>
          <Input
            id="manufacturer"
            value={data.manufacturer || ""}
            onChange={(e) => onChange({ ...data, manufacturer: e.target.value })}
            placeholder="e.g., Dell, HP, MINISFORUM"
            className={errors.manufacturer ? "border-red-500" : ""}
          />
        </div>
      )}

      {/* More optional fields */}
    </Form>
  );
}
```

#### 3.4 Modal Triggering

**File**: `apps/web/components/imports/ImportResultsGrid.tsx`

```typescript
// When import completes with quality="partial"
function ImportResultsGrid() {
  const [partialImport, setPartialImport] = useState<ImportSession | null>(null);

  useEffect(() => {
    const unsubscribe = subscribeToImportStatus((result) => {
      if (result.quality === "partial") {
        setPartialImport(result);
        // Modal auto-opens
      }
    });
    return unsubscribe;
  }, []);

  return (
    <>
      <ImportGrid results={importResults} />

      {partialImport && (
        <PartialImportModal
          importSession={partialImport}
          extractedData={partialImport.extracted_data}
          onComplete={async (data) => {
            await completePartialImport(partialImport.job_id, data);
            setPartialImport(null);
          }}
          onCancel={() => setPartialImport(null)}
        />
      )}
    </>
  );
}
```

### Phase 4: Frontend - Real-Time UI Updates

**Duration**: 2-3 days
**Deliverable**: Polling/WebSocket listener, toast notifications, grid updates

#### 4.1 Import Status Hook

**File**: `apps/web/hooks/useImportStatus.ts`

```typescript
export function useImportStatus(bulkJobId: string | null) {
  const [status, setStatus] = useState<BulkIngestionStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (!bulkJobId) return;

    setIsPolling(true);
    const pollInterval = setInterval(async () => {
      const response = await fetch(`/api/v1/ingest/bulk/${bulkJobId}/status`);
      const data = await response.json();
      setStatus(data);

      // Stop polling when all jobs complete
      if (data.status === "complete" || data.status === "partial" || data.status === "failed") {
        setIsPolling(false);
        clearInterval(pollInterval);
      }
    }, 1000); // Poll every 1 second

    return () => clearInterval(pollInterval);
  }, [bulkJobId]);

  return { status, isPolling };
}
```

#### 4.2 Toast Notifications

**File**: `apps/web/components/imports/ImportToasts.tsx`

```typescript
function ImportToasts({ status }: { status: BulkIngestionStatusResponse | null }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const previousStatus = useRef<PerRowStatus[]>([]);

  useEffect(() => {
    if (!status) return;

    // Find newly completed imports
    const newlyCompleted = status.per_row_status.filter(
      (current) => !previousStatus.current.find((p) => p.url === current.url)
    );

    newlyCompleted.forEach((completed) => {
      const toast: Toast = {
        id: completed.url,
        title: completed.status === "complete" ? "Import successful" : "Partial import",
        description: `${completed.status === "complete" ? "All" : "Some"} data imported from ${new URL(completed.url).hostname}`,
        action: {
          label: completed.status === "partial" ? "Complete" : "View",
          onClick: () => {
            if (completed.status === "partial") {
              // Show modal to complete
            } else {
              // Show details modal
            }
          }
        }
      };

      setToasts((prev) => [...prev, toast]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      }, 5000);
    });

    previousStatus.current = status.per_row_status;
  }, [status?.per_row_status]);

  return (
    <div className="fixed bottom-4 right-4 space-y-2">
      {toasts.map((toast) => (
        <div key={toast.id} className="bg-white rounded shadow-lg p-4">
          <p className="font-semibold">{toast.title}</p>
          <p className="text-sm text-gray-600">{toast.description}</p>
          <button
            onClick={toast.action.onClick}
            className="text-sm text-blue-600 hover:underline"
          >
            {toast.action.label}
          </button>
        </div>
      ))}
    </div>
  );
}
```

#### 4.3 Grid Real-Time Updates

**File**: `apps/web/components/imports/ImportGrid.tsx`

```typescript
export function ImportGrid() {
  const { bulkJobId } = useParams();
  const { status, isPolling } = useImportStatus(bulkJobId);

  return (
    <div>
      {/* Progress Bar */}
      {isPolling && status && (
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-2">
            <span>Import Progress</span>
            <span>
              {status.completed}/{status.total_urls}
              ({status.success} successful, {status.partial} partial)
            </span>
          </div>
          <progress
            value={status.completed}
            max={status.total_urls}
            className="w-full"
          />
        </div>
      )}

      {/* Results Table - Updates in real-time */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>URL</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Quality</TableHead>
            <TableHead>Listing</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {status?.per_row_status.map((row) => (
            <TableRow key={row.url} className={getRowClassName(row.status)}>
              <TableCell>{new URL(row.url).hostname}</TableCell>
              <TableCell>
                {row.status === "running" && <Spinner />}
                {row.status === "complete" && <CheckCircle />}
                {row.status === "partial" && <AlertCircle />}
                {row.status === "failed" && <XCircle />}
              </TableCell>
              <TableCell>{row.quality}</TableCell>
              <TableCell>
                {row.listing_id && (
                  <Link href={`/listings/${row.listing_id}`}>View</Link>
                )}
              </TableCell>
              <TableCell>
                {row.status === "partial" && (
                  <Button size="sm" onClick={() => openCompleteModal(row)}>
                    Complete
                  </Button>
                )}
                {row.error && (
                  <Button size="sm" variant="ghost" onClick={() => showError(row)}>
                    Error
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
```

#### 4.4 WebSocket Alternative (Optional Enhancement)

For real-time without polling overhead:
```typescript
export function useImportWebSocket(bulkJobId: string | null) {
  const [status, setStatus] = useState<BulkIngestionStatusResponse | null>(null);

  useEffect(() => {
    if (!bulkJobId) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/ingest/bulk/${bulkJobId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data);
    };

    return () => ws.close();
  }, [bulkJobId]);

  return { status };
}
```

---

## Design Specifications

### Modal Layout

**State 1: Extracted Data Display**
```
┌─────────────────────────────────────────┐
│ Complete Import                      ✕  │
├─────────────────────────────────────────┤
│                                         │
│ We extracted most data, but need help   │
│ with 1 field to complete this listing   │
│                                         │
│ ✓ EXTRACTED DATA                        │
│  • Title: Dell OptiPlex 7090 SFF        │
│  • Images: 4 images                     │
│  • CPU: Intel Core i5-10500 (6-core)   │
│  • RAM: 8GB DDR4                        │
│  • Storage: 512GB SSD                   │
│                                         │
│ ! COMPLETE THESE FIELDS                 │
│  • Price (Required) [________$]         │
│                                         │
│ [Cancel]  [Save Listing]                │
└─────────────────────────────────────────┘
```

**Field Highlighting:**
- **Green**: Extracted from source (read-only display)
- **Yellow**: User input required (editable with validation)
- **Red**: Validation error (show error message below)
- **Gray**: Optional fields (can skip)

### Toast Notifications

**Success (Full Import):**
```
┌──────────────────────────────────────┐
│ ✓ Import successful                  │
│   Dell OptiPlex 7090 imported from   │
│   ebay.com                           │
│                             [View]   │
└──────────────────────────────────────┘
```

**Partial Import:**
```
┌──────────────────────────────────────┐
│ ⚠ Partial import                     │
│   HP Mini PC needs price - fill it   │
│                             [Complete]│
└──────────────────────────────────────┘
```

**Error:**
```
┌──────────────────────────────────────┐
│ ✕ Import failed                      │
│   Could not extract title from URL   │
│                             [Retry]  │
└──────────────────────────────────────┘
```

### Grid Updates

**Progress Bar During Bulk Import:**
```
Import Progress
Completed 3 of 5 (2 successful, 1 partial)
[███████░░░░░░░░░░░░░░░░░░░░░░░░░] 60%
```

**Table Rows:**
- New row appears as "processing..." with spinner
- Row updates to "complete" with green checkmark
- Row updates to "partial" with yellow warning icon
- Row updates to "failed" with red X icon

**Color Coding:**
```
Complete  → Light green background
Partial   → Light yellow background
Failed    → Light red background
Running   → Light gray background with spinner
```

---

## Implementation Plan

### Phase 1: Backend - Partial Extraction Support
**Duration**: 2-3 days
**Owner**: Backend team

**Tasks:**
1. Update `NormalizedListingSchema` to make price optional with validation
2. Add minimum field validation (title OR cpu_model+manufacturer)
3. Update `BaseAdapter._validate_response()` to allow partial data
4. Create Alembic migration for nullable price and quality column
5. Update `ListingsService` to handle null prices
6. Update adapter implementations (eBay, JSON-LD, Scraper)
7. Update error responses to distinguish partial vs. failed
8. Add tests for partial extraction scenarios

**Testing:**
- Unit tests: Schema validation with null price
- Integration tests: Adapter extraction with various partial data
- E2E tests: Full import pipeline with missing price

### Phase 2: Backend - Real-Time Status Updates
**Duration**: 1-2 days
**Owner**: Backend team

**Tasks:**
1. Add status tracking columns to `ImportSession` model
2. Create bulk import status endpoint (`GET /api/v1/ingest/bulk/{id}/status`)
3. Update ingestion task to track status transitions
4. Add response schema `BulkIngestionStatusResponse`
5. Implement pagination for per-URL statuses
6. Add WebSocket endpoint for real-time updates (optional)
7. Add integration tests for status polling

**Testing:**
- Unit tests: Status endpoint returns correct data
- Integration tests: Status updates as imports complete
- Load tests: Status endpoint with 1000+ concurrent polls

### Phase 3: Frontend - Manual Population Modal
**Duration**: 2-3 days
**Owner**: Frontend team

**Tasks:**
1. Create `PartialImportModal` component
2. Create `ExtractedFieldsSection` display
3. Create `MissingFieldsForm` with validation
4. Implement form submission with `completePartialImport()` API call
5. Auto-open modal when import completes with quality="partial"
6. Add TypeScript types for partial import responses
7. Add Storybook stories for modal variants
8. Add accessibility: ARIA labels, keyboard navigation, screen reader support

**Testing:**
- Component tests: Modal renders correctly with various data states
- Integration tests: Modal submission saves complete listing
- E2E tests: User journey from import to modal to completion
- Accessibility tests: Keyboard navigation, screen reader support

### Phase 4: Frontend - Real-Time UI Updates
**Duration**: 2-3 days
**Owner**: Frontend team

**Tasks:**
1. Create `useImportStatus` hook for polling
2. Create `ImportToasts` component for notifications
3. Update `ImportGrid` to display real-time updates
4. Add progress bar showing completion percentage
5. Implement row highlighting for status changes
6. Add toast action buttons (View, Complete, Retry)
7. Implement WebSocket alternative (optional)
8. Add tests for polling and WebSocket

**Testing:**
- Hook tests: `useImportStatus` polls correctly
- Component tests: `ImportGrid` updates on status change
- E2E tests: Multi-URL import with real-time updates
- Performance tests: Polling doesn't cause UI lag

### Phase 5: Integration & Rollout
**Duration**: 1 day
**Owner**: Full team

**Tasks:**
1. End-to-end testing of all phases together
2. Feature flag configuration for rollout
3. Database migration deployment
4. Monitoring setup (success rate, partial rate, manual completion rate)
5. Documentation updates
6. Release notes and user communication

**Testing:**
- Full system E2E tests
- Staging environment validation
- Performance benchmarking
- Data quality validation

---

## Edge Cases & Error Handling

### Edge Case 1: No Fields Extracted Successfully

**Scenario**: Adapter extracts only images, no text data

**Current**: Import fails with "Missing required fields"
**New Behavior**:
- Validation error: "No title or CPU model extracted"
- Response status: `failed`
- Error message to user: "Could not extract listing information from this URL"
- Suggestion: "Try a different URL or add listing manually"

### Edge Case 2: Only CPU Model, No Title

**Scenario**: Amazon page with CPU details but title in JavaScript

**Current**: Import fails entirely
**New Behavior**:
- Validation passes: "Has cpu_model + manufacturer"
- Import succeeds with quality="partial"
- Modal shows: CPU/manufacturer extracted, requests title + price
- User enters: Title and price
- Result: Complete listing saved

### Edge Case 3: Price Invalid Format

**Scenario**: Price extracted as "£299.99" (pound sign) or "299,99" (comma separator)

**Current**: Import fails with schema validation error
**New Behavior**:
- Adapter attempts to parse price
- If parsing fails: Set price to null, add to extraction_metadata: `{"price": "extraction_failed"}`
- Import succeeds with quality="partial"
- User manually enters price in modal
- Result: Complete listing

### Edge Case 4: Duplicate with Partial Data

**Scenario**: Similar listing already exists but with different price

**Current**: May create duplicate
**New Behavior**:
- Check similarity using title + manufacturer
- If match found:
  - Show warning modal: "Similar listing found: [existing title]"
  - Offer options:
    - "Update existing listing with new price"
    - "Create new listing"
    - "Cancel import"
- If user updates: Merge data (prefer newly extracted over old)
- Track provenance: "Updated from Amazon [date]"

### Edge Case 5: User Abandons Modal

**Scenario**: Partial import modal appears, user closes it without completing

**Current**: N/A
**New Behavior**:
- Partial listing saved with incomplete data
- Marked as "needs_review" in database
- Filter in dashboard shows these partial listings
- User can return to complete later via "Review Partial Imports" view
- Toast offers "Complete later" or "Save as-is"

### Edge Case 6: Network Error During Manual Entry

**Scenario**: User fills modal form, submits, network fails

**Current**: N/A
**New Behavior**:
- Show error: "Could not save listing"
- Keep form data in browser (don't clear)
- Offer: "Retry" or "Save offline" (localStorage)
- On retry: Submit offline data
- If offline save: Show notification to user next session

### Edge Case 7: Stale Partial Import Modal

**Scenario**: User has modal open for 2 minutes, manually refreshes page

**Current**: N/A
**New Behavior**:
- Modal closed on page refresh
- Partial import still exists in database
- Dashboard shows "Incomplete imports" section
- User can click "Complete" to reopen modal
- Modal repopulates with original extracted data

### Edge Case 8: Concurrent Manual Completion

**Scenario**: User submits modal form twice quickly (double-click save)

**Current**: N/A
**New Behavior**:
- Button disabled after first click
- Loading state shown: "Saving..."
- Second click ignored
- Success toast shows once with listing view link

---

## Testing Strategy

### Unit Tests (Backend)

**File**: `tests/test_ingestion_partial.py`

```python
class TestPartialImportSupport:
    async def test_schema_allows_null_price(self):
        # price=None should validate
        schema = NormalizedListingSchema(
            title="Dell OptiPlex",
            price=None,  # This should not raise
            marketplace="amazon"
        )
        assert schema.price is None

    async def test_minimum_field_validation_title_only(self):
        # Title alone should pass
        schema = NormalizedListingSchema(
            title="PC with CPU",
            price=None,
            marketplace="amazon"
        )
        schema.validate_minimum_fields()  # Should not raise

    async def test_minimum_field_validation_cpu_manufacturer(self):
        # CPU + manufacturer without title should pass
        schema = NormalizedListingSchema(
            title=None,
            cpu_model="Intel i5-10500",
            manufacturer="Dell",
            price=None,
            marketplace="amazon"
        )
        schema.validate_minimum_fields()  # Should not raise

    async def test_minimum_field_validation_fails_no_required_fields(self):
        # Neither title nor cpu_model+mfg should fail
        schema = NormalizedListingSchema(
            title=None,
            cpu_model=None,
            manufacturer=None,
            price=None,
            marketplace="amazon"
        )
        with pytest.raises(ValueError, match="requires either title"):
            schema.validate_minimum_fields()

    async def test_adapter_allows_partial_extraction(self):
        # Adapter should not require price
        adapter = JsonLdAdapter()
        result = adapter._validate_response({
            "title": "Dell PC",
            "price": None,  # Missing price
        })
        # Should not raise AdapterException
```

### Integration Tests (Backend)

**File**: `tests/test_ingestion_integration_partial.py`

```python
class TestPartialImportIntegration:
    async def test_import_with_null_price_creates_listing(self, session):
        # Full flow: URL → adapter → null price → saved listing
        url = "https://amazon.com/dp/B08N5WRWNW"

        result = await ingestion_service.ingest(url, user_id="user123")

        assert result.status == "complete"
        assert result.quality == "partial"
        listing = await Listing.get(result.listing_id)
        assert listing.price_usd is None
        assert listing.title == "Dell OptiPlex 7090"

    async def test_metrics_not_calculated_for_null_price(self, session):
        # Listings with null price should not have valuation_breakdown
        url = "https://amazon.com/no-price"
        result = await ingestion_service.ingest(url, user_id="user123")

        listing = await Listing.get(result.listing_id)
        assert listing.adjusted_price_usd is None
        assert listing.valuation_breakdown is None

    async def test_bulk_import_partial_and_complete_mixed(self, session):
        # Bulk import with some partial, some complete
        urls = [
            "https://amazon.com/with-price",
            "https://amazon.com/no-price",
            "https://ebay.com/complete"
        ]

        result = await ingestion_service.bulk_ingest(urls, user_id="user123")

        status = await get_status(result.bulk_job_id)
        assert status.total_urls == 3
        assert status.success >= 1
        assert status.partial >= 1
```

### Component Tests (Frontend)

**File**: `apps/web/components/imports/__tests__/PartialImportModal.test.tsx`

```typescript
describe("PartialImportModal", () => {
  it("renders extracted fields as read-only", () => {
    const extractedData = {
      title: "Dell OptiPlex",
      images: ["img1.jpg"],
      cpu_model: "Intel i5",
      price: null,
    };

    render(
      <PartialImportModal
        importSession={mockSession}
        extractedData={extractedData}
        onComplete={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByText("Dell OptiPlex")).toBeInTheDocument();
    expect(screen.getByText("4 images")).toBeInTheDocument();
  });

  it("highlights missing fields", () => {
    render(<PartialImportModal {...props} />);

    const priceInput = screen.getByLabelText("Price (Required)");
    expect(priceInput).toHaveClass("border-yellow-400");
  });

  it("validates price before submission", async () => {
    render(<PartialImportModal {...props} />);

    const input = screen.getByLabelText("Price");
    await userEvent.type(input, "-100");

    await userEvent.click(screen.getByText("Save Listing"));

    expect(screen.getByText("Price must be positive")).toBeInTheDocument();
  });

  it("calls onComplete with filled data on save", async () => {
    const onComplete = vi.fn();
    render(
      <PartialImportModal
        {...props}
        onComplete={onComplete}
      />
    );

    await userEvent.type(screen.getByLabelText("Price"), "299.99");
    await userEvent.click(screen.getByText("Save Listing"));

    expect(onComplete).toHaveBeenCalledWith(
      expect.objectContaining({ price: 299.99 })
    );
  });
});
```

### E2E Tests

**File**: `tests/e2e/import_partial.spec.ts`

```typescript
describe("Partial Import E2E", () => {
  it("completes full flow: Amazon URL → partial import → manual completion", async ({
    page,
  }) => {
    // Navigate to import page
    await page.goto("/dashboard/import");

    // Enter URL without price data
    await page.fill('input[placeholder="Paste URL"]', "https://amazon.com/no-price");
    await page.click("button:has-text('Import')");

    // Wait for partial import result
    await expect(page.locator("text=Partial import")).toBeVisible();

    // Modal should auto-open
    await expect(page.locator("text=Complete Import")).toBeVisible();

    // View extracted data
    await expect(page.locator("text=Dell OptiPlex")).toBeVisible();

    // Fill missing price
    await page.fill('input[label="Price"]', "299.99");

    // Submit
    await page.click("button:has-text('Save Listing')");

    // Verify listing appears in grid
    await expect(page.locator("text=Dell OptiPlex")).toBeVisible();

    // Verify quality indicator
    await expect(page.locator("text=Price manually entered")).toBeVisible();
  });

  it("shows real-time updates for bulk import", async ({ page }) => {
    // Upload 3 URLs
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: "urls.csv",
      mimeType: "text/csv",
      buffer: Buffer.from("url\nhttps://ebay.com/1\nhttps://amazon.com/2\nhttps://amazon.com/3"),
    });

    // Watch progress update in real-time
    await expect(page.locator("text=/Completed 0 of 3/")).toBeVisible();

    // Wait for first result
    await page.waitForTimeout(2000);
    await expect(page.locator("text=/Completed 1 of 3/")).toBeVisible();

    // Toast appears for first result
    await expect(page.locator(".toast:has-text('Import successful')")).toBeVisible();

    // Can click "Complete" button on partial imports
    const completeButton = page.locator("button:has-text('Complete')").first();
    await completeButton.click();

    // Modal opens
    await expect(page.locator("text=Complete Import")).toBeVisible();
  });
});
```

---

## Rollout Plan

### Phase 1: Feature Flag Setup
- Add `FEATURE_PARTIAL_IMPORTS` flag to ApplicationSettings
- Default: `false` (disabled)
- Allow per-user override via settings

### Phase 2: Internal Testing
- Enable for dev/staging environment
- Internal team tests all scenarios
- Validate data quality
- Performance test: bulk imports with 100+ URLs

### Phase 3: Beta Users (Day 1-3)
- Enable for 5-10 beta users
- Monitor:
  - Partial import rate (expect 15-25%)
  - Manual completion rate (expect 70%+)
  - Data quality (validation errors <5%)
- Collect feedback via in-app survey

### Phase 4: Controlled Rollout (Week 1)
- Enable for 25% of users
- Monitor metrics
- Watch for errors in logs
- Adjust modal UX based on feedback

### Phase 5: Full Rollout (Week 2)
- Enable for 100% of users
- Feature flag becomes default
- Remove old all-or-nothing logic
- Celebrate improved import success rate!

### Monitoring Metrics

**Dashboard Metrics:**
- Import success rate (complete + partial) vs. failed
- Partial import rate (% of all imports)
- Manual completion rate (% of partial that are completed)
- Time to completion (extract time + manual entry time)
- Data quality score (validation errors, missing required fields)

**Error Tracking:**
- Adapter extraction failures by type (timeout, parse, rate limit)
- Modal validation errors by field
- API errors (500s, timeouts)

**User Behavior:**
- Modal dismissal rate (% who skip manual entry)
- Average manual entry time
- Duplicate detection hits
- Data quality trends over time

---

## Future Enhancements

### Post-MVP Features

**Bulk Manual Population (Phase 4+)**
- View all partial imports at once
- Fill multiple prices in table view
- Bulk submit all at once

**ML-Based Price Estimation (Phase 5+)**
- Suggest prices based on similar listings
- Learn from user corrections
- Auto-fill with confidence threshold

**Import Templates (Phase 5+)**
- Save extraction rules for frequent sources
- "Remember this Amazon format"
- Auto-apply next time

**Marketplace Native Integration (Phase 6+)**
- Official Amazon/Etsy APIs instead of scraping
- 100% extraction success
- Real-time price sync

**Mobile Companion App (Phase 6+)**
- Scan barcodes to import
- Auto-fill from phone camera
- Voice entry for manual fields

---

## Success Criteria

### Quantitative
- Import success rate: 80%+ (up from 30%)
- Partial import rate: 15-25% of all imports
- Manual completion rate: 70%+ of partial imports
- Data quality score: 90%+ (validation errors <5%)
- Modal open time to save: <2 minutes average
- Page refresh needed: 0 (100% real-time)

### Qualitative
- Users report improved import experience
- Support tickets for import failures: -50%
- Feature adoption: 80%+ of users enable feature
- Code quality: All tests passing, <5% bug rate in first 2 weeks

---

## Appendix: Related Documentation

- **Current Ingestion System**: `/docs/development/ingestion-architecture.md`
- **Adapter Implementation Guide**: `/docs/development/adapter-implementation.md`
- **API Schemas**: `packages/core/dealbrain_core/schemas/ingestion.py`
- **Frontend Import Component**: `apps/web/components/imports/`
- **Database Models**: `apps/api/dealbrain_api/models/core.py` (Listing, ImportSession)
