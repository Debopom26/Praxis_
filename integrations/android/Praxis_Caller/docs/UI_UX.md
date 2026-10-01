## Current implementation - 2026-09-29

Current implementation and host screenshot review are documented in PHASE_8_AUDIT.md. Test-rendered images under evidence/ui-host are labeled synthetic; no device or real Praxis result is claimed.

---

# UI / UX Specification

## Direction
Modern, dark, minimalist phone UI closely inspired by the interaction density of Samsung Phone / One UI, but implemented with original assets/components.

## In-call identity region
Contact photo
Contact name
Phone number
Praxis control/status directly beneath identity

## Praxis sequence
1. Connect to Praxis
2. three animated dots while connecting
3. Voice/Audio Orb when audio begins flowing
4. distinct Analysis/Decision Orb while analysis is active
5. risk color smoothly maps green -> yellow -> amber -> orange -> red
6. meaningful decision -> short notification sound
7. analysis orb shifts/shrinks left
8. textual analysis appears on right
9. future risk updates continue smoothly

## Orb A
Represents voice/audio flow and may react to audio energy.

## Orb B
Represents model/evidence analysis and decision formation.

Never remove one orb by merging both concepts unintentionally.

Use the user-supplied final reference image as visual source of truth.

## Inspected reference — Phase 0
User-identified source: `C:\Users\KIIT\Downloads\WhatsApp Image 2026-09-23 at 9.37.24 PM.jpeg`; preserved at `references/finalized-praxis-caller-ui.jpeg`.

Eight panels: dark recents list; identity/connect button; three-dot connecting pill; network-like voice visualization; separate dotted analysis orb; analysis-complete notification/orb; smaller orb left with green result card; same arrangement with red risk card. Portrait/name/number remain above Praxis, phone controls and prominent red end button below. Rounded dark cards, restrained green accents and a green-to-red orb align with the locked direction. A custom notification sound is indicated visually; no audio asset is supplied.

Names/numbers, 18/100 and 87/100 scores, authenticity/speaker/context labels are design examples, never runtime results. The source has evidence/risk fields, but does not guarantee every pictured label can be supported. Preserve both orb concepts. Pictured video/add-call icons do not by themselves prove Android capabilities or add implemented features. Phase 8 will reconcile details with real state/platform APIs; no UI code was created in Phase 0.

## Phase 1 scope
Minimal dark Material3 base, original vector launcher, Phone/Call/Praxis navigation and Recents/Contacts/Keypad tabs. Keypad changes only a saved draft. Empty lists and disabled call/end/connect controls explicitly describe unavailability. Content scrolls within system/bar insets; no reference scores, demo contacts, fake calls or timers appear. Final orb layouts, animation and notification sound remain Phase 8, not Phase 1 acceptance. Host Compose tests exercise navigation and Activity recreation; no physical screen/layout test has been claimed.
