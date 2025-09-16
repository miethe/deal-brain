import { ProfileList } from "../../components/profiles/profile-list";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";

export default function ProfilesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Scoring profiles</h1>
        <p className="text-sm text-muted-foreground">Tune how the composite score behaves for Proxmox, Plex, or dev workloads.</p>
      </div>
      <ProfileList />
      <Card>
        <CardHeader>
          <CardTitle>Tip</CardTitle>
          <CardDescription>Profiles drive rankings and dashboard cards.</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          API support for creating/updating profiles is live. The UI wiring for editing weights will follow once we
          introduce slider controls and optimistic updates.
        </CardContent>
      </Card>
    </div>
  );
}
