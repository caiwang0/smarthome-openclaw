Now I have a complete picture. Let me produce the sprint contract.

---

# 🏠 SmartHub Dashboard — Design Sprint Contract

## Current State Audit

The existing dashboard has a **brutalist/industrial hacker aesthetic** that violates nearly every principle for a consumer home product:

| Problem | Current | Impact |
|---|---|---|
| Font | JetBrains Mono (monospace) everywhere | Feels like a terminal, not a home |
| Background | `#0A0A0A` (near-black) | Cold, hostile, banned by brief |
| Accent | `#CCFF00` acid green | Neon/toxic feeling, not warm |
| Border-radius | `0 !important` globally forced | Sharp, industrial, unwelcoming |
| Card gap | `2px` | Cramped, no breathing room |
| Room headers | 12px uppercase monospace | Invisible from any distance |
| MAC/IP shown | By default on every card | Technical jargon, intimidating |
| Text sizes | Multiple `10px` labels | Below 14px minimum |
| Touch targets | Volume buttons at 36px (w-9) | Below 44px minimum |
| Typography | ALL CAPS TRACKING EVERYWHERE | Feels like shouting, not a home |

---

## 1. Design Direction

**Feeling:** *"Coming home and everything just works."*

Imagine walking into a warm, well-lit kitchen. The counters are clean, things are where you expect them. You don't have to think — you just *know* where things are. That's this dashboard.

- **Calm confidence** — not flashy, not techy. Quiet competence.
- **Lived-in warmth** — soft surfaces, round edges, natural colors like linen and wood.
- **Effortless clarity** — your eyes go to what matters (what's ON) without scanning.
- **Touch-friendly generosity** — big targets, generous spacing, forgiving of imprecise taps.

The reference mood is: **an IKEA catalog page meets Apple Home** — Scandinavian warmth, consumer-grade simplicity, zero jargon.

---

## 2. Color Palette

### Base Colors (Warm Light Theme)
| Token | Hex | Usage |
|---|---|---|
| `--bg-primary` | `#FAF8F5` | Page background (warm off-white, like linen) |
| `--bg-card` | `#FFFFFF` | Card surfaces |
| `--bg-card-active` | `#FFF8ED` | Cards with active devices (warm glow) |
| `--border-subtle` | `#E8E2D9` | Card borders, dividers |
| `--border-active` | `#E8913A` | Active device card accent border |
| `--text-primary` | `#2C2520` | Headings, device names |
| `--text-secondary` | `#8C7E72` | Labels, secondary info |
| `--text-muted` | `#B8ADA2` | Timestamps, metadata |

### Semantic Colors
| Token | Hex | Usage |
|---|---|---|
| `--device-on` | `#E8913A` | Warm amber — device is ON, active indicator |
| `--device-on-bg` | `#FFF3E0` | Light amber wash behind active cards |
| `--device-off` | `#B8ADA2` | Muted taupe — device is OFF |
| `--toggle-on-bg` | `#E8913A` | Toggle track when ON |
| `--toggle-off-bg` | `#D9D2CA` | Toggle track when OFF |
| `--heat` | `#E8653A` | Climate heating mode (warm red-orange) |
| `--cool` | `#5BA4CF` | Climate cooling mode (calm blue) |
| `--warning` | `#D4760A` | Low battery, warnings |
| `--danger` | `#C93B3B` | Offline, errors |
| `--success` | `#5A9E6F` | Online status dot |
| `--room-header` | `#6B5E52` | Room name text |

### Why these colors work:
- The amber `#E8913A` is the hero color — it reads as "warmth" and "light on" simultaneously
- The warm off-whites (`#FAF8F5`) feel like paper or linen, not clinical
- No cold grays — every neutral has a warm brown undertone
- The palette passes WCAG AA contrast for all text on its respective backgrounds

---

## 3. Typography

**Font: [Nunito Sans](https://fonts.google.com/specimen/Nunito+Sans)**

| Why Nunito Sans | |
|---|---|
| Rounded terminals | Feels friendly and approachable |
| Excellent readability | Clear at 14px AND 48px |
| Multiple weights | 400 (body), 600 (labels), 700 (headings) |
| Free on Google Fonts | No licensing issues |
| Not overused in tech | Doesn't scream "startup" or "bank" |

### Type Scale (8px-grid aligned)
| Role | Size | Weight | Line-height | Usage |
|---|---|---|---|---|
| Room Header | `24px` / `1.5rem` | 700 | 32px | Room section titles — visible from 1m+ |
| Device Name | `16px` / `1rem` | 600 | 24px | Card title — primary scanning target |
| Body / Value | `16px` / `1rem` | 400 | 24px | Sensor values, status text |
| Label | `14px` / `0.875rem` | 600 | 20px | "Brightness", "Volume", filter tabs |
| Caption | `14px` / `0.875rem` | 400 | 20px | Manufacturer, secondary info |

**No text below 14px anywhere.** The current `10px` labels are completely eliminated.

---

## 4. Layout

### Page Structure
```
┌──────────────────────────────────────────┐
│  🏠 My Home              [3 active]      │  ← Warm header, device summary
│  ─────────────────────────────────────── │
│  [All] [Living Room] [Kitchen] [Bedroom] │  ← Room pill tabs (scrollable)
├──────────────────────────────────────────┤
│                                          │
│  Living Room                             │  ← Room header: 24px, bold
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ 💡      │ │ 🔌      │ │ 🌡️      │   │
│  │ Ceiling │ │ Fan     │ │ Thermo  │   │  ← Cards: rounded-2xl, shadow-sm
│  │ Light   │ │         │ │ stat    │   │
│  │ ● ON    │ │ ○ OFF   │ │ 22°C   │   │
│  │ [━━━━]  │ │ [toggle]│ │ [+-]   │   │
│  └─────────┘ └─────────┘ └─────────┘   │
│                                          │
│  Kitchen                                 │
│  ┌─────────┐ ┌─────────┐               │
│  │ ...     │ │ ...     │               │
│  └─────────┘ └─────────┘               │
└──────────────────────────────────────────┘
```

### Grid
- **Desktop (≥1280px):** 4 columns, `16px` gap
- **Laptop (≥1024px):** 3 columns, `16px` gap
- **Tablet (≥640px):** 2 columns, `12px` gap
- **Phone (<640px):** 1 column, `12px` gap

### Card Design by Device Type
- **All cards:** `rounded-2xl`, `padding: 20px`, `shadow-sm`, white background
- **Active cards:** Warm amber left border (4px), light amber background tint (`#FFF8ED`), subtle `shadow-md`
- **Light cards:** Toggle + brightness slider when on. Slider track fills with amber.
- **Switch cards:** Large toggle — the entire card tap-target area triggers toggle.
- **Climate cards:** Prominent current temp (32px), target temp with +/- buttons (48px touch targets)
- **Camera cards:** Rounded snapshot preview, tap to enlarge with smooth overlay
- **Sensor cards:** Large value readout (20px), icon + label on left, value on right
- **Media player cards:** Play/pause as large circular button (56px), volume rocker with clear icons

### Visual Hierarchy (what your eye hits, in order):
1. **Room name** (biggest text on screen)
2. **Active device cards** (amber glow pulls the eye)
3. **Device names** within cards
4. **Device state** (ON/OFF, temperature values)
5. **Controls** (toggles, sliders, buttons)
6. **Secondary info** (manufacturer, if shown at all)

---

## 5. Interaction Design

### Toggle Behavior
- **Track size:** `52px × 28px` (comfortably above 44px touch minimum)
- **Thumb:** `24px` circle, white with subtle shadow
- **ON state:** Amber track (`#E8913A`), thumb slides right with spring easing (250ms)
- **OFF state:** Warm gray track (`#D9D2CA`), thumb slides left
- **Optimistic update:** Toggle flips immediately on tap, reverts if API fails
- **Disabled state:** 50% opacity, cursor-not-allowed

### Tap/Click States
- **Card press:** Subtle scale(0.98) transform on active, 150ms
- **Button press:** Scale(0.95) + slightly darker background, 100ms
- **Toggle press:** Slight thumb squish (scaleX: 1.1), satisfying micro-interaction

### Hover States (desktop only)
- **Card hover:** Lift with `shadow-md`, border darkens slightly, 200ms transition
- **Button hover:** Background darkens one shade, 150ms
- **No hover dependency:** Everything works by tap alone — hover is enhancement only

### Animations
- **Card entry:** Fade in + slide up 8px, staggered 50ms per card, 250ms duration, ease-out
- **State change:** Background color crossfade 250ms
- **Slider dragging:** Real-time thumb tracking, debounced API call (300ms)
- **Toast notification:** Slide in from right, auto-dismiss 8s, slide out

### Touch Targets
Every interactive element meets the **44px minimum**:
| Element | Current Size | New Size |
|---|---|---|
| Toggle switch | 44×22px | 52×28px (plus padding = 52×44px hit area) |
| Volume -/+ | 36×36px | 48×48px |
| Climate -/+ | 40×40px | 48×48px |
| Play/Pause | 48×48px | 56×56px |
| Room filter pills | ~32px height | 40px height + 12px padding |
| Card entire surface | N/A | Clickable for primary action (toggleable devices) |

---

## 6. Component-by-Component Changes

### `index.html`
- Replace JetBrains Mono Google Font link with Nunito Sans (`wght@400;600;700`)
- Update `<title>` to "My Home"

### `tailwind.config.js`
- Replace `fontFamily.mono` and `fontFamily.sans` with `["Nunito Sans", "system-ui", "sans-serif"]`
- Remove the monospace font entirely
- Update color tokens to new warm palette
- Add `rounded-2xl` as default card radius token
- Add `slide-up` keyframe animation (translateY 8px → 0, opacity 0 → 1)
- Keep `fade-in` animation but extend to 250ms

### `src/index.css`
- **Remove** `border-radius: 0 !important` — this is the single most impactful line to delete
- Change `body` background from `#0A0A0A` to `#FAF8F5`
- Change `body` font-family to `"Nunito Sans", system-ui, sans-serif`
- Change `body` color to `#2C2520`
- Restyle `.card` class:
  - `background: #FFFFFF`
  - `border: 1px solid #E8E2D9`
  - `border-radius: 16px` (2xl)
  - `padding: 20px`
  - `box-shadow: 0 1px 3px rgba(44, 37, 32, 0.06)`
  - `transition: box-shadow 0.2s, border-color 0.2s, background 0.25s`
- Restyle `.card:hover`: `box-shadow: 0 4px 12px rgba(44, 37, 32, 0.1)`, `border-color: #D9D2CA`
- Restyle `.card-active`:
  - `background: #FFF8ED`
  - `border-color: #E8913A`
  - `border-left-width: 4px`
  - `box-shadow: 0 4px 12px rgba(232, 145, 58, 0.12)`
- Restyle `.btn`:
  - Remove monospace font
  - `font-family: "Nunito Sans"`, `font-size: 14px`, `font-weight: 600`
  - `border-radius: 12px`, `padding: 8px 16px`
  - `background: #FFFFFF`, `border: 1px solid #E8E2D9`, `color: #6B5E52`
  - Remove `text-transform: uppercase` and `letter-spacing`
- Restyle `.btn:hover`: `background: #F5F0EB`, `border-color: #D9D2CA`
- Restyle `.btn-active`: `background: #FFF3E0`, `border-color: #E8913A`, `color: #E8913A`
- Restyle `.toggle-track`:
  - `width: 52px`, `height: 28px`, `border-radius: 14px`
  - `border: none`, `background: #D9D2CA`
  - `transition: background 0.25s ease`
- `.toggle-track[data-on="true"]`: `background: #E8913A`
- Restyle `.toggle-thumb`:
  - `width: 24px`, `height: 24px`, `border-radius: 12px`
  - `background: #FFFFFF`, `box-shadow: 0 1px 3px rgba(0,0,0,0.15)`
  - `transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)` (spring easing)
- `.toggle-track[data-on="true"] .toggle-thumb`: `transform: translateX(24px)`
- `.toggle-track[data-on="false"] .toggle-thumb`: `background: #FFFFFF` (not gray)
- Restyle range slider thumb and track with warm amber colors, rounded
- Restyle scrollbar with warm tones

### `src/App.tsx`
- Change outer div from `bg-[#0A0A0A] text-[#F5F5F0] font-mono` → `bg-[#FAF8F5] text-[#2C2520] font-sans`
- Replace header:
  - Remove `border-l-4 border-[#BFFF00]` (not a progress bar)
  - `h1`: Change from "SMARTHUB" uppercase monospace → "My Home" in 24px/700 weight, warm brown `#2C2520`
  - Subtitle: Show active device count in friendly language: "3 lights on · 22°C inside" — not "47 devices"
  - Remove the harsh divider line, use subtle `border-b border-[#E8E2D9]` instead
  - `bg-[#FAF8F5]` with subtle bottom shadow on scroll

### `src/components/AreaFilter.tsx`
- Change from joined brutalist button strip → **pill tabs** with rounded corners and generous padding
- Each pill: `rounded-full`, `px-4 py-2`, min-height 40px
- Active pill: amber background `#FFF3E0`, amber text `#D4760A`, amber border
- Inactive pill: white background, warm gray border, warm gray text
- Add horizontal scroll with `overflow-x-auto` and `scrollbar-hide` for mobile
- Remove device counts from pills (simplify — counts add clutter for regular users)
- Remove "Unassigned" pill — regular users don't understand this concept. Show unassigned devices under an "Other" section instead.

### `src/components/DeviceCard.tsx`
- **Remove MAC/IP address display entirely** — technical jargon, banned. No user needs this.
- Remove the "NEW" badge brutalist styling → soft amber rounded badge with house icon
- Change device name from `text-sm font-mono` → `text-base font-semibold font-sans text-[#2C2520]`
- Manufacturer text: `text-sm text-[#8C7E72]` (14px minimum, no 10px)
- Remove `font-mono` from every text element
- Icon + name should be left-aligned, status badge right-aligned, vertically centered

### `src/components/DeviceGrid.tsx`
- Room headers: `text-2xl font-bold text-[#6B5E52]` (24px, prominent)
  - Remove `border-l-2 border-[#BFFF00]` left accent
  - Add warm emoji prefix per room type (optional) or just bold text
  - Add `mb-4` spacing below header
- Card grid gap: `gap-4` (16px) instead of `gap-[2px]`
- Empty state: Friendly illustration/message — "No devices here yet" with warm icon, not a brutalist grid SVG
- Animation: `animate-slide-up` with proper spring easing

### `src/components/StatusBadge.tsx`
- Online: Small green dot (`#5A9E6F`), no text label (reduce clutter — a green dot is universally understood)
- Offline: Small red dot (`#C93B3B`) + "Offline" text (this IS important to communicate)
- Unknown: Small gray dot (`#B8ADA2`), no label
- Remove `font-mono`, `uppercase`, `tracking-wide`
- Dot size: `8px × 8px` with `rounded-full`
- Online dot gets a subtle pulse animation (not aggressive blink)

### `src/components/LightCard.tsx`
- State label: "On · 75%" or "Off" in `text-sm` warm colors — no monospace
- Toggle: Uses new warm toggle styles (52×28px)
- Brightness slider:
  - Track: `6px` height, warm gray, filled portion in amber
  - Thumb: `20px` circle, white with shadow, rounded
  - Replace the thin divider line above slider with natural spacing
  - Label "Brightness" in `14px` warm gray
  - Value "75%" in `16px` semibold amber when on

### `src/components/SwitchCard.tsx`
- Same toggle restyling as LightCard
- State: "On" / "Off" in friendly text, amber/gray
- Larger touch target — the row itself should be tappable

### `src/components/ClimateCard.tsx`
- Current temp: Prominent `20px` readout, e.g., "Currently 21°C"
- Target temp: Large `32px` bold value, colored by mode (amber for heat, blue for cool)
- +/- buttons: `48×48px`, `rounded-xl`, warm styling
- Mode buttons: Pill-shaped, `rounded-full`, with friendly labels (capitalize "Heat", "Cool", "Auto", "Off")
- Remove `font-mono` from all text
- Replace `text-[10px]` labels with `14px`

### `src/components/CameraCard.tsx`
- Snapshot: `rounded-xl` corners, no harsh 2px border
- Hover overlay: Semi-transparent warm overlay with "Tap to expand" or expand icon
- Enlarged view: Warm dark overlay (`rgba(44,37,32, 0.9)`) not pure black, rounded image, close button in corner
- Camera name in enlarged view: `16px` warm text, not tiny uppercase monospace

### `src/components/SensorCard.tsx`
- Each sensor row: `min-height: 40px` for touch targets
- Labels: `14px` (not 10px), warm gray, sentence case (not uppercase)
- Values: `16px` semibold, warm brown for normal, amber for warnings
- Binary sensor states: Friendly labels remain, but styled warmer
- Low battery: Amber warning icon, not aggressive red (red = truly broken)
- High temp: Warm amber indicator

### `src/components/MediaPlayerCard.tsx`
- Play/Pause button: `56×56px` circular, amber background, white icon, `rounded-full`
- Volume buttons: `48×48px`, rounded, warm gray
- "Now playing" text: `14px` amber, truncated with ellipsis
- Remove ALL monospace and uppercase from labels
- Volume display: "Volume 65%" in `14px` warm gray

### `src/components/NotificationToast.tsx`
- Rounded card (`rounded-2xl`) with warm amber left stripe
- White background with subtle shadow
- "New device found!" in friendly 16px semibold (not uppercase screaming)
- Device name in amber
- Smooth slide-in from top-right, fade out
- Close button: `32×32px` touch target, warm gray X icon

### `src/components/DeviceIcon.tsx`
- Change active color from `#BFFF00` → `#E8913A` (warm amber)
- Change inactive color from `#6B6B6B` → `#B8ADA2` (warm muted)
- Increase icon size from `w-5 h-5` → `w-6 h-6` (24px) for better visibility
- SensorIcon: Increase from `w-4 h-4` → `w-5 h-5` (20px)

---

## 7. Acceptance Criteria

### Usability
- [ ] **AC-1:** A user can identify which devices are ON within 2 seconds of seeing the page (active cards have amber glow + border that pops against the warm white background)
- [ ] **AC-2:** Every toggle touch target is at least 44×44px (verified via dev tools element inspector)
- [ ] **AC-3:** Toggling a light or switch requires exactly ONE tap (no expand-first, no confirmation dialog)
- [ ] **AC-4:** No text in the UI is smaller than 14px (verified via computed styles)
- [ ] **AC-5:** No technical jargon (entity_id, MAC, IP) is visible anywhere on the default view
- [ ] **AC-6:** No monospace font appears anywhere in the rendered UI

### Warmth
- [ ] **AC-7:** Page background is warm off-white (#FAF8F5), not black or cold gray
- [ ] **AC-8:** All card corners are rounded (border-radius ≥ 12px)
- [ ] **AC-9:** The accent color for active devices is warm amber (#E8913A), not acid green
- [ ] **AC-10:** The font is Nunito Sans (or equivalent friendly sans-serif), not monospace

### Glanceability
- [ ] **AC-11:** Room names are readable from 1 meter away on a 10" tablet (24px bold minimum)
- [ ] **AC-12:** Active device cards are visually distinguishable from inactive ones at arm's length (background tint + border color change)
- [ ] **AC-13:** Temperature values on climate/sensor cards are ≥20px
- [ ] **AC-14:** Offline devices show a clear but non-alarming red dot indicator

### Polish
- [ ] **AC-15:** Toggle animations use eased transitions of 200-300ms (not instant, not sluggish)
- [ ] **AC-16:** Card hover on desktop produces a subtle lift (shadow increase) within 200ms
- [ ] **AC-17:** Cards enter the viewport with a staggered fade+slide animation
- [ ] **AC-18:** All spacing follows an 8px grid (4, 8, 12, 16, 20, 24, 32, 40, 48px)
- [ ] **AC-19:** Empty/loading states show friendly messages, not blank screens or spinners
- [ ] **AC-20:** The page title is "My Home", not "SMARTHUB"

---

## 8. Implementation Order

Each phase builds on the previous. **Ship after each phase — every phase is independently valuable.**

### Phase 1: Foundation (highest impact, changes everything) 
**Files:** `index.html`, `tailwind.config.js`, `src/index.css`
- Swap font from JetBrains Mono → Nunito Sans
- Replace entire color palette (background, text, borders)
- Remove `border-radius: 0 !important`
- Restyle `.card`, `.btn`, `.toggle-*` classes
- Restyle range slider
- **Result:** The entire app transforms from "hacker terminal" to "warm home" in one shot. Every component inherits the new foundation.

### Phase 2: Layout & Hierarchy 
**Files:** `src/App.tsx`, `src/components/DeviceGrid.tsx`, `src/components/AreaFilter.tsx`
- New header with "My Home" and friendly summary
- Room headers at 24px bold
- Grid gap from 2px → 16px
- Room filter pills restyled
- Empty state redesign
- **Result:** Spatial hierarchy feels like a real home app. Rooms are scannable.

### Phase 3: Card Content Cleanup 
**Files:** `src/components/DeviceCard.tsx`, `src/components/StatusBadge.tsx`, `src/components/DeviceIcon.tsx`
- Remove MAC/IP address display
- Fix all font sizes to ≥14px
- Remove all `font-mono`, `uppercase`, `tracking-wide`
- New icon colors (amber active, warm gray inactive)
- Redesigned status badge (dot only for online)
- **Result:** Every card reads like a consumer product. No jargon.

### Phase 4: Device Controls Polish 
**Files:** `src/components/LightCard.tsx`, `src/components/SwitchCard.tsx`, `src/components/ClimateCard.tsx`
- Toggle restyled (52×28px, spring animation)
- Brightness slider with amber fill
- Climate temp display at 32px
- Touch targets verified at 48px
- **Result:** Core controls feel satisfying and accessible.

### Phase 5: Specialty Cards 
**Files:** `src/components/MediaPlayerCard.tsx`, `src/components/CameraCard.tsx`, `src/components/SensorCard.tsx`
- Media player: Large play button, warm styling
- Camera: Rounded preview, warm overlay
- Sensors: 14px+ labels, warm value colors
- **Result:** Every device type feels polished.

### Phase 6: Notifications & Final Polish 
**Files:** `src/components/NotificationToast.tsx`
- Toast redesign with warm styling
- Final animation tuning
- Spacing audit (8px grid compliance)
- Cross-browser/device testing pass
- **Result:** Ship-ready. Proud to show friends.

---

## Summary

This redesign transforms the dashboard from a **developer's terminal** into a **product people love using**. The warm amber palette, generous spacing, rounded shapes, and friendly typography all serve one goal: **making your home feel as approachable on screen as it does in person.**

The current brutalist aesthetic (black background, acid green, monospace, zero border-radius, MAC addresses) communicates "this is for engineers." The new design communicates "this is for *you*." That's the difference between a tech demo and a product.