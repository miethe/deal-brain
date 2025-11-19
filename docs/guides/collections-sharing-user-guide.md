---
title: "Collections & Sharing User Guide"
description: "Comprehensive guide for end users on how to use Deal Brain's Collections and Sharing features including organizing deals, sharing with others, and comparing PCs."
audience: [users, ai-agents]
tags: [user-guide, collections, sharing, deals, how-to, tutorial]
created: 2025-11-18
updated: 2025-11-18
category: "user-documentation"
status: published
related:
  - /docs/api/collections-sharing-api.md
  - /docs/development/collections-sharing-developer-guide.md
---

# Collections & Sharing User Guide

## Welcome to Collections & Sharing

Deal Brain's Collections and Sharing features help you organize PC listings, share amazing deals with friends, and collaboratively compare different configurations. This guide covers all the features you need to get the most out of your deal hunting.

---

## Quick Start

### Create Your First Collection

1. **Navigate to Collections** - Click "Collections" in the sidebar
2. **Click "New Collection"** button
3. **Enter details:**
   - **Name** (required): Something descriptive like "Gaming Builds" or "Office PCs"
   - **Description** (optional): Add context about this collection
   - **Visibility** (default: Private): Keep it personal or share with others
4. **Click "Create"** - Your collection is ready!

### Add Deals to Collections

**Method 1: From Listing Page**
1. Find a deal you like
2. Click **"Add to Collection"**
3. Select which collection (or create a new one)
4. Click **"Add"**

**Method 2: While Browsing**
1. When viewing a shared deal
2. Click **"Add to Collection"**
3. Select target collection

**Method 3: From Share Link**
1. Open a shared link
2. Click **"Add to Collection"**
3. Choose where to save it

---

## Organizing Your Collections

### What You Can Track

Each item in your collection can track:

**Status** - Where you are in the buying process:
- **Undecided** - Still evaluating
- **Shortlisted** - Top candidates you're seriously considering
- **Rejected** - Ruled out (too expensive, wrong specs, etc.)
- **Bought** - Already purchased!

**Notes** - Personal observations:
- Pros and cons
- Why you like/dislike it
- Comparison notes
- Purchase date and price paid

**Position** - Organize items by:
- Drag-and-drop ordering
- Priority ranking
- Grouping by category

### Updating Items

**Change Status:**
1. Open your collection
2. Click the item status
3. Select new status
4. Changes save automatically

**Add/Edit Notes:**
1. Click the item to expand
2. Click the notes field
3. Type your observations
4. Save when done

**Reorder Items:**
1. Click and drag items to reorder
2. Positioning saves automatically

### Managing Collections

**Rename Collection:**
1. Click collection name
2. Click edit icon
3. Change name or description
4. Save changes

**Change Visibility:**
1. Open collection settings
2. Change from Private → Unlisted → Public
3. Save

**Delete Collection:**
1. Click collection options (three dots)
2. Select "Delete"
3. Confirm deletion
4. All items in collection are deleted too

---

## Sharing Deals

### Why Share?

- Get second opinions on deals
- Collaborate with friends on PC builds
- Share amazing finds
- Track what you've shared with whom

### Public Share Links

Perfect for sharing on social media, forums, or messaging apps.

**Generate a Public Link:**
1. Find the deal you want to share
2. Click **"Share"** button
3. Click **"Copy Link"** tab
4. Click **"Generate Link"** (if needed)
5. **Copy** the link
6. **Share anywhere**: Discord, Reddit, X, Facebook, etc.

**Public Link Features:**
- No login required to view
- Shows deal details and pricing
- Tracks how many people viewed it
- Works forever (until you delete it)
- Great for social media sharing

**Example public link:**
```
https://dealbrain.com/deals/123/abc123def456xyz789...
```

### User-to-User Sharing

Direct sharing with other Deal Brain users - perfect for personal recommendations.

**Send a Share:**
1. Find the deal
2. Click **"Share"** button
3. Click **"Share with User"** tab
4. **Search for recipient** by username
5. **(Optional) Add a message** - "Check this out!" or "What do you think?"
6. Click **"Send"**

**What Happens:**
- Recipient gets a notification
- They receive your message with the deal link
- They can view the deal immediately
- They can add it to one of their collections
- You'll see if they've viewed and imported it

**Share Expiry:**
- User shares last for 30 days
- After expiry, data is archived
- Recipient can still access older shares

### Tracking Shares

**See What You've Shared:**
1. Go to your profile or settings
2. Look for "Shares" or "Shared Deals"
3. View list of everyone you've shared with
4. See view counts and import status

**Manage Your Shares:**
- Delete shares you no longer want to track
- View recipient feedback
- See import history

---

## Receiving Shared Deals

### Notification Inbox

When someone shares with you or imports something you shared:

**Your Notifications:**
1. Click the **bell icon** in the header
2. See all notifications with previews
3. Unread shares have a dot indicator
4. Click to view full details

### Shared Deal Preview

When you receive a user share:
1. Click the notification
2. See the deal details
3. Sender's optional message appears
4. Click **"Add to Collection"** to save it
5. View details and decide if you want it

### Importing Shares

**Quick Import:**
1. Open the shared deal
2. Click **"Add to Collection"**
3. Select a collection (or create new one)
4. Click **"Import"**
5. Deal now appears in your collection

**The Sender Knows:**
- When you view their share
- When you import it to your collection
- They see import notifications

---

## Comparing Deals

### Using Collections for Comparison

**Build Your Comparison:**
1. Create a collection for this comparison
2. Add 3-5 deals you're considering
3. Use **"Comparison View"** if available

**Information Displayed:**
- Price (highlighted by deal quality)
- CPU and GPU
- Performance metrics ($/CPU Mark)
- Score rating
- Your notes and status

### Filtering and Sorting

**In Your Collection:**
- **Sort by:** Price, performance, status, date added
- **Filter by:** CPU family, price range, GPU type
- **Search:** Quick lookup by title

### Export for Offline Review

**Download as CSV (for spreadsheets):**
1. Open collection
2. Click **"Export"**
3. Choose **CSV** format
4. Download `collection_1.csv`
5. Open in Excel, Google Sheets, etc.

**Download as JSON (for data):**
1. Open collection
2. Click **"Export"**
3. Choose **JSON** format
4. Download `collection_1.json`
5. Use for integration with other tools

**CSV includes:**
- Title and price
- CPU and GPU
- Performance metrics
- Your status and notes

**JSON includes:**
- Full collection metadata
- All items with complete details
- Listing information
- Perfect for programmatic access

---

## Tips & Best Practices

### Organization Strategies

**Strategy 1: By Build Type**
Create separate collections for different PC categories:
- Gaming (RTX 4080, high performance)
- Office (productivity, quiet)
- Server (multi-thread, workstation)
- Budget (sub-$500, value-focused)

**Strategy 2: By Status**
Use collection visibility to track decision stage:
- Private: Early research
- Unlisted: Narrowed down (shareable with specific people)
- Public: Final recommendations (share with everyone)

**Strategy 3: By Timeline**
Create collections by timeframe:
- Black Friday Deals
- January Sales
- Summer Gaming PCs

### Effective Noting

**Good Notes Include:**
- Specific reasons (e.g., "Great single-thread performance")
- Comparisons (e.g., "$200 cheaper than Model X")
- Concerns (e.g., "No warranty, from 3rd party seller")
- Research links (e.g., "Benchmark scores: CPU Mark 18,500")
- Purchase intent (e.g., "Perfect for gaming, considering buying")

**Before Final Decision:**
1. Review all shortlisted items
2. Compare prices and specs
3. Check return policies
4. Export final candidates
5. Share with trusted friends for feedback

### Collaboration Tips

**Finding the Right Deal:**
1. Share collection with team/friends
2. Let them review and add their thoughts
3. Export comparison to group chat
4. Discuss offline, update notes
5. Eventually mark as "bought" when decision is made

**Getting Feedback:**
1. Create collection with favorites
2. Share link with specific people
3. Ask them to add notes
4. Review their feedback
5. Decide together

**Tracking Group Purchases:**
1. Create shared collection
2. Add deals everyone is considering
3. Update status when people buy
4. Keep notes about conditions/sellers
5. Archive when group shopping is done

---

## Common Questions

### Q: Can I share a collection instead of individual deals?

**A:** Not directly, but you can:
1. Export your collection as JSON or CSV
2. Share the file with others
3. They can import it locally or reference your public collection link
4. Coming soon: Direct collection sharing

### Q: Who can see my private collections?

**A:** Only you! Private collections are:
- Invisible to other users
- Not searchable
- Cannot be found via link
- Completely personal

### Q: What happens if I delete a collection?

**A:** All items in that collection are permanently deleted:
- Notes are lost
- Items are removed from your collection
- You cannot recover them
- Consider exporting first if unsure

### Q: How long do shares last?

**A:** It depends on share type:
- **Public shares:** Forever (until you delete them)
- **User-to-user shares:** 30 days (data archived after)
- **Collection links:** Depend on your visibility setting

### Q: Can I share a collection with someone?

**A:** Currently:
- Make collection "Unlisted" or "Public"
- Generate a link to the collection page
- Share that link
- Coming soon: Direct collection sharing with specific users

### Q: Do recipients get notified when I share?

**A:** Yes!
- User-to-user shares send notifications
- Public link shares don't notify
- Notifications appear in their inbox
- Recipients see your message (if included)

### Q: Can I edit a share after sending it?

**A:** No, but you can:
- Delete and resend if needed
- Add context in a follow-up message
- Update your collection and re-share link

### Q: How do I know if someone viewed my share?

**A:** Check your notifications:
1. Go to Notifications
2. Look for "viewed" status
3. See import notifications if they added to collection
4. Track in share history

---

## Troubleshooting

### "Can't add item to collection"

**Possible causes:**
- Item already in that collection
- Listing doesn't exist
- Collection is full (if there's a limit)

**Solution:**
1. Check if item is already there (look in collection)
2. Try creating a new collection
3. Refresh page and retry

### "Share link not working"

**Possible causes:**
- Link expired (30 days for user shares)
- Share was deleted
- Incorrect link

**Solution:**
1. Request sender to resend
2. Check share expiry date
3. Ask for public link instead of user share

### "Can't find recipient when sharing"

**Possible causes:**
- Username spelled wrong
- User doesn't exist
- User has private account

**Solution:**
1. Double-check username spelling
2. Ask them their exact username
3. Verify they have an account

### "Export file is empty or corrupted"

**Possible causes:**
- Collection has no items
- Browser download issue
- Collection was deleted

**Solution:**
1. Make sure collection has items
2. Try exporting again
3. Try different format (CSV vs JSON)
4. Check browser download settings

### "Notifications not appearing"

**Possible causes:**
- Notifications disabled in settings
- Browser notification permissions not granted
- Email notifications not configured

**Solution:**
1. Check notification settings
2. Grant browser notification permissions
3. Check email spam folder
4. Wait a moment (some delays are normal)

---

## Getting Help

**Need more assistance?**
- Check this guide again for your question
- Look at in-app tooltips and help text
- Contact support: support@dealbrain.com
- Join the Deal Brain community discussions

---

## What's Next?

Now that you understand Collections & Sharing:

1. **Create your first collection** - Start organizing your favorite deals
2. **Share with a friend** - Let them see what you found
3. **Use comparisons** - Side-by-side evaluate options
4. **Export and analyze** - Make informed decisions

**Happy deal hunting!**
