# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Three core actions:
The first is the ability to enter owner and pet information. 
Second, the ability to add and edit care tasks.
Third, generate and view a daily plan.

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
    My first design has five classes:

        - Owner is the person using the app. It stores their name, how many minutes they have each day, and their preferences. It also holds their list of pets.
        - Pet is the animal. It stores the pet's name, species, age, and any special needs. It also holds that pet's list of tasks.
        - Task is one care activity, like a walk or a feeding. It stores a title, a category, how long it takes, how important it is, and whether it's done.
        - Scheduler is the "brain." It looks at the owner's tasks and time limit, then decides what goes into the day.
        - DailyPlan is the result. It lists what got scheduled, what got skipped, and why.

    An Owner has Pets, and a Pet has Tasks. The Scheduler uses the Owner and creates a DailyPlan. I kept the planning logic in the Scheduler, so the other classes only hold data. That keeps the design simple and easy to test.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Tradeoff: conflict detection checks exact start times, not overlapping durations.**

`Scheduler.find_conflicts()` groups pending tasks by `(due_date, preferred_time)` and warns when two or more share a slot. It does not compare durations, so a 30-minute walk at 07:30 and a feeding at 07:45 are not flagged, even though they overlap. A true overlap check would parse each `"HH:MM"` string into minutes, compute start and end times, sort by start, and compare neighbours.

I kept the exact-match version because:

- **Preferred times are wishes, not bookings.** The scheduler fills the owner's available minutes by priority. It does not build a timeline, so there is no real "end time" for an overlap to run into.
- **The data supports it.** Times are plain `"HH:MM"` strings with no validation. An overlap check built on them would fail on input like `"7:30"`, so it would need time parsing and validation first.
- **It is easy to explain.** The warning says "two tasks both want 17:00", and the owner can fix it at a glance. It never blocks the plan, so a false negative costs little.

The cost is missed overlaps. If PawPal+ grows into a real timeline, this is the first thing to upgrade.

**Reviewing the code for readability.** I asked for a simpler or faster version of `find_conflicts`. The one change I kept was swapping `slots.setdefault(key, []).append(...)` for a `defaultdict(list)`, which reads more directly and does the same work. I rejected a fully compressed version that built the whole warning list in one nested comprehension. It was shorter but harder to follow, because the same-pet versus cross-pet message logic ended up inside the comprehension. Performance was not a reason to change anything. The method is already linear in the number of tasks plus the number of conflicting pairs.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used Claude Code in small, specific steps instead of one big request: first class skeletons from my UML, then filling in the core logic, then a demo script (`main.py`), then two tests, then docstrings, then the README. The most helpful prompts named exact requirements. For example, I told it that `Owner` needs one method returning every pet's tasks (`get_all_tasks`) and that `Scheduler` must read from that method, not from a single pet. That kept the AI from taking the shortcut of scheduling for one pet. Small, scoped requests were also easy to check one at a time.

**What the AI suggested**

- It filled in the skeleton methods: validation in `Task`, duplicate-id rejection in `Pet.add_task`, and `Owner.get_all_tasks()` flattening all pets' tasks.
- It built `Scheduler.generate_plan()` as a greedy planner. It sorts pending tasks by priority, then preferred time, then shortest duration, and fills the owner's available minutes in that order.
- It added `description` and `frequency` fields to `Task`, because my task list called for them and the skeleton lacked them.
- It added an optional `scheduled` flag to `DailyPlan.add_entry` so the same method can record skipped tasks.
- It pointed out a flaw in its own design. Task ids are only unique within one pet, but `DailyPlan.explanations` is keyed by task id, so two pets with the same id would overwrite each other's explanations.

**What I accepted or rejected**

- I accepted the greedy, priority-first approach because it is simple, predictable and easy to explain to a pet owner. The cost is that it can skip a long high-value task while squeezing in shorter, lower-priority ones.
- I accepted the extra `Task` fields and the `add_entry` change because they came straight from the requirements.
- I did not accept the id-collision issue as fine. I recorded it as a known limitation in the README instead of leaving it hidden. I have not fixed it yet. The fix would be globally unique ids, or keying explanations by the task object.
- I held the AI to the scope I asked for. `app.py` is still not connected to the classes, and the tests cover only two behaviors, because those were the steps I requested.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

The clearest moment was the id-collision problem. The AI's code worked for my demo, where task ids are 1 to 5 across both pets, so it would have been easy to move on. I treated the AI's own warning as a real design bug and documented it instead of assuming the demo proved the design correct.

To verify the AI's work, I did not rely on its description. I ran things:

- I ran `python3 main.py` and checked that the schedule had all five tasks in time order, with a 90-minute total matching the 90 minutes available. The earlier two-pet check also showed the 40-minute grooming task being skipped once the time ran out, with the reason stated.
- I ran `pytest`. The two tests check that `mark_complete()` flips `is_completed` and that `add_task` increases a pet's task count. Both pass.
- After the docstring pass I re-ran the tests and the demo to confirm nothing about the behavior had changed.

These checks show the basic behavior works. They do not cover edge cases such as ties in priority, zero available minutes or tasks with no preferred time.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
