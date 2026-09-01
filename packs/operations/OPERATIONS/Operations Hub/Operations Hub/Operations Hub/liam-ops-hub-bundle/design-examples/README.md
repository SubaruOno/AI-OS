# Design reference pages

Five full working pages, one per direction. Open them in a browser and pick a favourite before you
brief your agent. Read `../reference/design-directions.md` for the process around them.

| File | Direction |
|---|---|
| `swiss-light.html` | Quiet Swiss. Light, calm, hairline borders, mono labels |
| `terminal-dark.html` | Terminal dark. Near-black, one bright accent, dense |
| `control-panel.html` | Control panel. Panel edges, status chips, colour encodes state |
| `product-dark.html` | Product dark. Rounded cards, gradients, polished |
| `bold-contrast.html` | High contrast bold. Heavy type, flat colour, large numerals |

## These are scrubbed copies

Each one started as a real design and was rewritten before landing here. Removed across the set:

- Real people: names, a phone number, Instagram and LinkedIn profiles. All social links now go to `#`.
- Real companies and product brands, replaced with neutral placeholders.
- A live Google Analytics measurement tag and its whole script block.
- Nine third-party hosted images (a storage bucket belonging to someone else's project, a stock photo
  service, a random-avatar service), each replaced with an inline grey placeholder so the pages don't
  call out to anyone.

No credentials, keys or tokens were present in any of them, which was checked rather than assumed.

## They need a network connection

Every page still pulls its CSS framework, icon set and fonts from public CDNs. They render fine with
a connection and look broken without one. That's acceptable for a page you're looking at once to pick
a direction, and it is **not** a pattern to copy into your own app. One font link is enough there.

## What was left out, and why

**A purchased commercial template (9 files) was excluded entirely.** Its licence permits use in your
own products and client projects, but explicitly forbids reselling or redistributing the template and
sharing the template files publicly. Putting it in a folder that gets zipped and passed to someone
else is exactly that. Scrubbing doesn't change a licence, so it isn't here.

**Three further pages were dropped:** a tour operator's site, an artist's portfolio and a campaign
page for a real energy company. All three were the most heavily tied to a real identity and the
weakest fit for an internal ops tool, so the trim and the scrub agreed.

If you want any of the excluded looks, describe it to your agent and have it generate a fresh page.
That's better anyway, because it comes out already full of your own content.
