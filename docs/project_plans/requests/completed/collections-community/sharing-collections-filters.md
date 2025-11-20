# New Sharing, Collections, and Filters Features

Created Date: 11-12-25

The following requests are proposed to improve the user experience and functionality of the application. Each item needs to be evaluated and designed thoroughly for implementation into the app. The implementation of each should then be planned.

## Enhancements

- Preparing for our release prior to Black Friday, I want to add new features that set the stage for a more community-focused experience.

### Sharing

- Sharing: allow users to share their favorite deals with others:
    - This should support multiple outputs, including a shareable "Card" which can be posted on social media or via email, or even as html on a webpage.
    - Should support a listing export, which can be imported into another instance of the app.

### Collections

- Collections: allow users to create collections of listings:
    - Users can create named collections (e.g., "My Holiday Deals", "Workstation Builds", etc.)
    - Users can add/remove listings to/from collections.
    - Collections can be shared as a whole, similar to individual listings.
    - Collections should support sorting and filtering within them.
- There should be a new dedicated Collections page, accessible from the main navigation sidebar, which allows users to create, view, and manage their collections:
    - This page should show each collection as a Card which contains the relevant high-level details: name, description, and number of listings, etc. There should also be a color option, which will be used as an indicator for that collection elsewhere in the app.
    - Clicking the card should open the Collection Modal, showing the Collection details at the top and a list of all listings within that collection, with options to sort and filter. Each listing should be clickable to navigate the user to that listing's detail page.
    - There should also be an "Expand" button which opens the Collection detail page, showing the full details of the collection and its listings in a larger format. In the future, this may also support additional features, such as analytics, trends, etc.
- Collections should also be added to the /listings page catalog view via a colored bar at the top of each listing card, indicating which collection(s) that listing belongs to. 
    - Hovering over the bar should show a tooltip with the collection name(s)
    - Users should be able to click on the collection name(s) in the tooltip to navigate to the corresponding collection page.
    - Listings should be filterable by Collections with a new filter option per below.

### Filters

- Move the existing filters in the /listings top bar into the sidebar, to allow for more advanced filtering options and better organization.
    - The filter section should be a new collapsible panel in the sidebar, labeled "Filters". It should sit within a dedicated section of the existing sidebar, below the navigation links and above the "Quick actions" section.
    - The filter panel should contain all existing filter options from the top toolbar, as well as new options based on available data for listings.
    - The filters should be organized into collapsible, logical categories (e.g., Price, Specs, Condition, etc.) for better usability. Each would bundle related filters together. For example, "Price" would contain Min/Max price sliders for listing price and adjusted value, as well as for $ / Passmark scores, etc.
- Add a new filter option for Collections, similar to a Tag Cloud filter, with each existing Collection represented as a colored box (same color as the indicator on the listing card) with the collection name inside it. Users can click on one or more collection boxes to filter listings to only those that belong to the selected collections.
    - The Collection filter should support multi-select, allowing users to filter by multiple collections at once.
    - The Collection filter should also support a "Select All" and "Clear All" option for ease of use.
