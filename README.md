# NIGHT 13 — The Guest Register

A small Python pixel-horror escape game set in a three-floor hotel. Draw an identity, investigate six residents, recover a checkout code and survive the final hunt.

The interface, story and documentation are in English. All visuals are drawn in code with Tkinter; no third-party packages, downloaded art, network connection or audio are required.

## Run

Use **Python 3.9 or newer with Tkinter**. Keep `main.py`, `engine.py` and `story.py` together, then run:

```sh
python3 main.py
```

In IntelliJ IDEA, open the whole folder, select a valid Python interpreter and run `main.py`. On macOS, use a Python distribution that includes working Tk support, such as the python.org installer. Some system Python installations have incompatible Tk builds.

## Controls

| Key | Action |
| --- | --- |
| Enter | Check in, accept an identity, confirm the elevator code |
| WASD / arrow keys | Move |
| E | Inspect a nearby object, speak, or use stairs |
| 1 / 2 / 3 | Choose a dialogue option |
| 0 / Esc | Leave a conversation |
| Q | Use your identity skill |
| F | Burn one match to freeze all pursuers for seven seconds |
| J | Open the journal; left/right arrows turn pages |
| B | Open inventory; on the title screen, open the hub |
| Esc | Pause or close a menu |

Release action keys before pressing them again. Held movement keys can repeat. Reading, dialogue, inventory, the journal and pause menus stop the chase and the warning-light animation. There is no global deadline: chase events are triggered by the story.

## The hotel

Each floor has two guest rooms to the north and a staff area to the south. Stairs are at the two ends of the corridor: right goes up, left goes down. Approach and press E.

Speak to the night attendant in the lower-left area of Floor 1. Inspect evidence in each room, then show it to that resident to collect a testimony. The evidence and testimonies are recorded in the journal.

Floor 1 is initially safe. On Floor 2, ordinary conversation with Shen Yan is safe; handing over his defaced photographs triggers a brief jump scare and a persistent chase. Read the code clue on the photographs before handing them over. He follows you through the stairs between floors.

The manager waits in the Floor 3 staff area. He does not disappear or attack merely because you enter. Collect all six testimonies, complete your identity mission, then speak to him and choose how to confront him. The correct response earns the keycard **and triggers the final lockdown**: the manager and all residents except the mother join the cross-floor hunt. Flickering lamps and red warning light accompany this stage. Reach the Floor 1 elevator and submit the code to escape.

Each pursuer walks towards a staircase before changing floors; they do not teleport onto the player. You have three health points and a brief protection period after a hit. Use matches and room barricades to create space.

## Identities

- **Night Clerk / Room Register:** mark the current floor's residents and clues for ten seconds, three uses. Each use adds five seconds to the run clock, which does not trigger pursuit. Mission: read the Floor 1 handover book and collect six testimonies.
- **Maintenance Worker / Barricade:** seal a nearby guest-room doorway for ten seconds, two uses. It blocks both you and pursuers. Mission: take the Floor 2 toolbox and repair the Floor 3 power box.
- **Amnesiac Guest / Memory Echo:** read an undiscovered clue within three tiles, three uses. Sight shrinks for ten seconds afterwards. Mission: find your old photograph on Floor 3.

## Endings and local saves

- **The Missing Guest:** lose all three health points.
- **The Next Game:** finish the investigation and use the elevator without confronting the manager successfully.
- **The Broken Register:** confront the manager correctly, survive lockdown and escape with the keycard.

`user_data/endings.json` stores unlocked endings, the fewest steps in a successful run and the Master Keycard. The current run is not saved. Old compatible ending archives are preserved; old wins do not retroactively award the new relic.

The hub displays the one carry-over relic. It does not stack. **A second instance is not implemented**, so the keycard cannot yet be used or consumed. `user_data/run_events.jsonl` records future endings and callback errors for local troubleshooting. Neither file belongs in the source submission or repository.

The game includes a short jump scare and fluctuating lighting during the final chase.

## Files and programming concepts

- `main.py`: keyboard input, scene transitions, timing and Canvas graphics.
- `engine.py`: state model, breadth-first pathfinding, skills, pursuit, dialogue gates and atomic save writes.
- `story.py`: identity descriptions, resident stories and clue text.
- `test_engine.py`: complete playable routes, trigger and pursuit checks, save behavior and input regressions.

The project uses classes/dataclasses, dictionaries and sets, file I/O with JSON, exception handling, grid pathfinding and an event-driven GUI.

## Tests

From the project folder:

```sh
python3 -m unittest discover -v
```

The automated checks include all three identity routes, cross-floor pursuit, the final lockdown, the mother's exemption, the manager's dialogue gate, the handover jump-scare transition and prevention of held Enter skipping the ending. GUI-state smoke checks use a headless Canvas stand-in; actual appearance should also be checked on a desktop.

<details>
<summary>Walkthrough hints — spoilers</summary>

Floor 1: three seats minus one = **2**. Floor 2: seven candles minus two = **5**. Floor 3: thirteen cards minus six = **7**. The other resident on each floor confirms the digit or ordering. The code is **257**, in ascending floor order.

For the true ending, restore the six names and refuse to sign the seventh line when speaking to the manager. Knowing the code alone does not bypass the six testimonies and role mission.

</details>
