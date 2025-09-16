import { AddListingForm } from "../../../components/listings/add-listing-form";

export default function NewListingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Add listing</h1>
        <p className="text-sm text-muted-foreground">Capture a deal and let the backend normalize and score it immediately.</p>
      </div>
      <AddListingForm />
    </div>
  );
}
