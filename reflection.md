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

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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
