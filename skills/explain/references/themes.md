# Theme packs & casting guide

## Two kinds of theme

**1. A specific world** (a TV show, film or series, a game, a book, a league or team): **use its real cast.** Name the characters, places, objects and famous moments, and cast each one by the trait that matches the code's behaviour. Generic stand-ins ("the managing partner", "a hero", "the drop zone") are a failure when the user named a specific world.

**2. A general topic** (cricket, cooking, cars, school, a city): use the packs below, written in the real vocabulary that people who love the topic use.

Fuzzy matches to packs: "IPL" → cricket, "F1" → racing, "iPhone / Android" → smartphone.
A specific game, show or team is case 1, even when a pack is close: "PUBG" still uses Erangel, Pochinki and the blue zone, not only the generic battle-royale pack.

**Rules for both:**
- Only use details a fan would recognise immediately. If unsure, look it up or leave it out. Never invent lore.
- Cast by behaviour. The reader should learn what the code *does* from who plays it.
- One cast member per part, used the same way everywhere.
- Keep the project's own names (its AI persona, product names) and attach the cast role once: "Vela (the app's AI, played by Harvey)".
- Allowed: names, roles, personalities, places, objects, and famous situations retold in your own words. Not allowed: logos, images, lyrics, scripts, long quotes.

## Worked example: a specific TV show (*Suits*)

Theme brief (what fans know): Pearson Hardman law firm in New York. **Harvey Specter**, the firm's best closer, wins the cases nobody else can. **Mike Ross** has a photographic memory and reads and remembers everything instantly (and secretly has no law degree). **Donna Paulsen**, Harvey's assistant, knows everything going on and decides who gets in to see Harvey. **Jessica Pearson**, the managing partner, has the final say over everyone. **Louis Litt** is obsessed with billable hours and the firm's money. **Rachel Zane** is the paralegal who digs up research. **Harold** is the clumsy junior associate. **Daniel Hardman** is the partner who secretly stole from the firm. Also: the file room, the associates' bullpen, and the mock trial.

Casting for a typical web app:

| Real part | Cast | Why it fits (the teaching point) |
|---|---|---|
| AI / core engine that produces the answer | Harvey Specter | Takes the hardest case and delivers the winning answer |
| Text/image reading (OCR, parsing) | Mike Ross | Reads every page instantly and remembers it all |
| Router / API entry | Donna Paulsen | Knows every request and decides who it goes to |
| Admin panel | Jessica Pearson's office | Final say over everyone and everything in the firm |
| Billing, usage limits, credits | Louis Litt | Counts every billable hour and charges for it |
| Search / data lookups | Rachel Zane | Digs up exactly the records you ask for |
| Database | The Pearson Hardman file room | Every case file is stored here |
| Background jobs | Associates working overnight in the bullpen | Work done after hours, out of sight |
| Tests | Mock trial | Practise the case before the real court |
| Malicious code / insider threat | Daniel Hardman | Someone inside the firm, secretly working against it |
| Hidden risk that could sink the project | Mike's fake law degree | A secret that, once found, threatens everything |
| A bug | One of Harold's blunders | An honest mistake that causes a mess |

Example sentence (eli5 + plain):
- 🧒 "Louis Litt counts every case review a client uses. But if a client knocks on two doors at the same moment, Louis only counts one."
- 👉 "Users who send two requests at the exact same time can get extra free analyses."

## Worked example: a specific game (*PUBG*)

Use real names: the plane drop, **Erangel** / **Miramar** maps, **Pochinki** (busy hot-drop town), **the blue zone** (shrinking safe area), **red zone** bombardment, **airdrops** (late, valuable supplies), **Level 3 helmet** (best protection), **backpack**, **revive**, **squad**, **"winner winner chicken dinner"**.
Casting ideas: entry/router → the plane and drop choice; rate limiting → the blue zone squeezing players; background jobs → airdrops; auth → squad lobby invite; a security hole → a hacker with wall-hacks; a crash under load → everyone hot-dropping into Pochinki.

---

## 🏏 cricket
- App: a cricket stadium on match day
- Users: fans and players
- Frontend / UI: the stands, the big screen and the scoreboard: what fans see
- Server / API: the umpires who take every request and decide what happens
- Routes / endpoints: the gates into the stadium, each with a sign
- Auth / login: security at the gate checking tickets and passes
- Database: the official scorebook: every run and wicket written down forever
- Cache: the quick-glance scoreboard (fast, but copied from the scorebook)
- Background jobs / queues: the ground staff working between overs
- External services: the TV broadcaster and other boards you depend on
- Payments: the ticket counter: real money becomes a seat
- Email / notifications: the stadium announcer
- Config / env / secrets: the dressing-room locker with the keys
- Logs / monitoring: the third umpire's replays
- Tests: nets practice before the match
- Deployment: walking out onto the pitch for the real match
- Bug: a dropped catch
- Security hole: a gap in the fence where anyone can sneak in
- Bottleneck: one slow bowler holding up the whole over
- Unfinished feature: a stand still under construction
- Tech debt: a pitch nobody has rolled in months

## ⚽ football
- App: a football club on match day · Users: fans, players, staff
- Frontend: the pitch and the stands, what everyone watches · Server/API: the referee team
- Routes: tunnel entrances · Auth: the steward checking accreditation
- Database: the club's record book · Cache: the half-time summary board
- Jobs: the groundskeepers working overnight · External: the league and broadcasters
- Payments: the ticket office and club shop · Notifications: the stadium speaker
- Secrets: the manager's tactics folder · Logs: VAR replays · Tests: training sessions
- Deployment: kick-off · Bug: an own goal · Security hole: an unguarded goal
- Bottleneck: everyone queuing at one turnstile · Unfinished: a stand covered in scaffolding · Tech debt: a muddy, patched-up pitch

## 🚗 cars
- App: a car · Users: the driver and passengers
- Frontend: the dashboard, steering wheel and pedals · Server/API: the engine control unit taking every input
- Routes: the buttons and levers, each doing one job · Auth: the car key and immobiliser
- Database: the fuel tank and the logbook · Cache: the small reserve tank for quick acceleration
- Jobs: the cooling fan that runs after you park · External: the petrol station, GPS satellites
- Payments: the fuel pump card reader · Notifications: dashboard warning lights
- Secrets: the spare key hidden in the garage · Logs: the black box / OBD reader · Tests: the test drive
- Deployment: driving out of the showroom · Bug: a rattle under the bonnet · Security hole: a door that doesn't lock
- Bottleneck: a clogged fuel line · Unfinished: a seat with no seatbelt yet · Tech debt: an overdue service

## 🏎️ racing (F1)
- App: a racing team on race weekend · Users: the driver and the fans
- Frontend: the steering wheel full of buttons + TV graphics · Server/API: the pit wall making every call
- Routes: radio channels · Auth: the paddock pass check
- Database: the telemetry archive · Cache: the live timing screen
- Jobs: the mechanics' overnight rebuild · External: tyre suppliers, race control
- Payments: sponsorship deals · Notifications: team radio
- Secrets: the setup sheet nobody else may see · Logs: telemetry traces · Tests: practice sessions
- Deployment: lights out, race start · Bug: a loose wheel nut · Security hole: a rival team reading your radio
- Bottleneck: a slow pit stop · Unfinished: an upgrade package still in the factory · Tech debt: last year's chassis held together with tape

## 🎯 battle-royale game
- App: the island match · Users: players dropping in
- Frontend: the lobby, HUD and map · Server/API: the game server deciding everything
- Routes: drop zones, places you can land · Auth: the player ID check before spawn
- Database: the loot crates and players' saved inventory · Cache: your backpack (quick access)
- Jobs: airdrops: they arrive later, not instantly · External: voice chat and the store servers
- Payments: the in-game shop: real money becomes skins · Notifications: the kill feed and alerts
- Secrets: the admin console password · Logs: the match replay · Tests: the training ground
- Deployment: the new season going live · Bug: a glitch that lets you fall through the floor
- Security hole: a wall hack: someone sees or does what they shouldn't · Bottleneck: lag when everyone lands in one place
- Unfinished: a fenced-off area of the map "coming soon" · Tech debt: old map parts patched over and over

## 🦸 superhero movies
- App: a hero team's headquarters · Users: citizens asking for help
- Frontend: the public face, the suits and the press conference · Server/API: mission control dispatching heroes
- Routes: emergency hotlines, one per type of trouble · Auth: the retina scan at the HQ door
- Database: the archive vault of every case file · Cache: the hero's quick-reference wrist screen
- Jobs: side missions done off-screen · External: allies from other teams
- Payments: the funding from the billionaire backer · Notifications: the signal in the sky
- Secrets: secret identities · Logs: security-camera footage · Tests: the training simulator
- Deployment: suiting up for the real battle · Bug: a suit malfunction mid-flight
- Security hole: a villain with a copied access card · Bottleneck: only one hero who can do a key job
- Unfinished: a prototype suit still in the lab · Tech debt: a base built in a hurry after the last attack

## 🍳 restaurant / cooking
- App: a restaurant · Users: diners
- Frontend: the dining room and the menu · Server/API: the waiter taking orders to the kitchen
- Routes: menu items, each one a different dish to request · Auth: the reservation check at the door
- Database: the pantry and recipe book · Cache: ingredients prepped on the counter
- Jobs: the overnight dough rising · External: suppliers and delivery riders
- Payments: the bill and card machine · Notifications: "order up!" bell
- Secrets: the secret sauce recipe · Logs: the kitchen order tickets · Tests: tasting before serving
- Deployment: opening night · Bug: salt instead of sugar · Security hole: the back door left open
- Bottleneck: one chef doing all the cooking · Unfinished: a dish on the menu the kitchen can't make yet · Tech debt: a grill nobody has cleaned

## 📱 smartphone
- App: a phone · Users: the owner
- Frontend: the touchscreen and app icons · Server/API: the processor handling every tap
- Routes: the apps and buttons, each doing one job · Auth: face unlock / fingerprint
- Database: storage, where photos and messages live · Cache: recent apps kept warm in memory
- Jobs: background app refresh · External: the cloud, cell towers, app store
- Payments: tap-to-pay wallet · Notifications: notification banners
- Secrets: the passcode and saved passwords · Logs: the activity history · Tests: the factory check before shipping
- Deployment: a software update rolling out · Bug: an app that crashes · Security hole: an app that can read your messages without asking
- Bottleneck: full storage slowing everything · Unfinished: a "coming soon" feature greyed out · Tech debt: ten-year-old apps nobody updates

## 🏫 school
- App: a school · Users: students and parents
- Frontend: classrooms and the notice board · Server/API: the school office handling every request
- Routes: office windows (admissions, fees, results) · Auth: the ID card at the gate
- Database: the register and report cards · Cache: the teacher's quick notes
- Jobs: homework checked after school · External: the exam board, the bus company
- Payments: the fee counter · Notifications: the school bell and circulars
- Secrets: the exam paper locked in the cupboard · Logs: the attendance register · Tests: mock exams
- Deployment: the first day of term · Bug: a wrong mark on a report card · Security hole: a student who can change their own marks
- Bottleneck: one office clerk for the whole school · Unfinished: the new lab still being built · Tech debt: old textbooks nobody replaced

## 🏙️ city (default)
- App: a city · Users: citizens
- Frontend: streets, shops and signs: what people see · Server/API: city hall handling requests
- Routes: roads to each department · Auth: ID check at the government building
- Database: the city records office · Cache: the info kiosk with popular answers
- Jobs: night-shift workers (garbage collection, street cleaning) · External: other cities, the power company
- Payments: the bank and tax office · Notifications: public announcements
- Secrets: keys to the city vault · Logs: CCTV · Tests: fire drills
- Deployment: opening a new district · Bug: a broken traffic light · Security hole: an unlocked vault door
- Bottleneck: a single bridge everyone must cross · Unfinished: a road that ends in a construction site · Tech debt: old pipes under the streets
