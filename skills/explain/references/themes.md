# Theme packs

Use a pack when the user's theme matches one (fuzzy match: "IPL" → cricket, "F1" → racing, "PUBG / Free Fire / Fortnite" → battle-royale, "Marvel / DC / Avengers" → superhero-movies, "iPhone / Android" → smartphone). For any other theme, build a map **in the same spirit**: pick things from that world a child would recognise, and make each analogy *explain the behaviour* of the part, not just sound cute.

Only use the rows for parts the project actually has. Change wording to fit the project, e.g. for a food-delivery app the "database" in cricket can be "the scorebook of every order".

**Text only.** Refer to franchises by general concepts (a drop zone, a hero team, a pit stop), never by copied characters' lines, logos or long quotes.

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
