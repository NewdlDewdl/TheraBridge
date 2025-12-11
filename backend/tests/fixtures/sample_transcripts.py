"""
Sample therapy session transcripts for testing
"""

SAMPLE_TRANSCRIPT_1 = """
Therapist: Hi Sarah, good to see you. How have you been since our last session?

Patient: It's been a rough week honestly. Work has been really stressful. My manager assigned me this huge project with an impossible deadline, and I've been staying late every night.

Therapist: That sounds exhausting. How has that been affecting you?

Patient: I haven't been sleeping well. I keep waking up at 3am thinking about everything I need to do. And then I'm exhausted during the day but can't focus.

Therapist: The sleep disruption is significant. Last time we talked about the box breathing technique. Have you had a chance to try that when you wake up at night?

Patient: I tried it a couple times. It helped a little, but then my mind just goes right back to the work stuff.

Therapist: That's actually good progress - you tried it and noticed some benefit. The racing thoughts are hard. What specifically runs through your mind?

Patient: Mostly that I'm going to fail. That everyone will see I can't handle this. My manager already seems disappointed in me.

Therapist: Those sound like some pretty harsh self-judgments. Do you have evidence that your manager is disappointed?

Patient: Not really... she hasn't said anything negative. I guess I just assume because she's been quiet.

Therapist: That's an interesting observation. We call that mind-reading in CBT - assuming we know what others think without evidence. What might be another explanation for her being quiet?

Patient: I guess she could just be busy too. Everyone's stressed about this project.

Therapist: Exactly. I'd like you to try something this week. When you notice yourself assuming the worst about what others think, pause and ask yourself - what's the evidence? And what's another possible explanation?

Patient: Okay, I can try that.

Therapist: Great. And for the sleep - let's add something. When you wake up at 3am, try the box breathing first, then if your mind is still racing, get up and write down your worries for 5 minutes. Get them out of your head and onto paper. Then go back to bed.

Patient: That's interesting. I've never tried writing them down.

Therapist: It can help externalize the worries so they're not spinning in your head. How are you feeling right now, talking about all this?

Patient: A little better actually. It helps to talk about it and have some things to try.

Therapist: I'm glad. You're dealing with a lot, and you're showing up and working on it. That takes strength. Same time next week?

Patient: Yes, that works. Thank you.
"""

EXPECTED_EXTRACTION_1 = {
    "key_topics": [
        "Work stress and deadline pressure",
        "Sleep disruption and insomnia",
        "Self-critical thoughts and catastrophizing",
        "Cognitive distortions (mind-reading)"
    ],
    "strategies": [
        {
            "name": "Box breathing",
            "category": "Breathing technique",
            "status": "reviewed",
            "context": "Patient tried it for nighttime waking, found it somewhat helpful"
        },
        {
            "name": "Cognitive restructuring - evidence checking",
            "category": "Cognitive",
            "status": "introduced",
            "context": "Identifying mind-reading and checking evidence for assumptions"
        },
        {
            "name": "Worry journaling",
            "category": "Behavioral",
            "status": "assigned",
            "context": "Write down worries when waking at 3am to externalize thoughts"
        }
    ],
    "triggers": [
        {
            "trigger": "Work deadlines and high-pressure projects",
            "context": "Large project with tight deadline causing stress and sleep issues",
            "severity": "moderate"
        },
        {
            "trigger": "Perceived manager disappointment",
            "context": "Manager's quietness interpreted as negative feedback",
            "severity": "mild"
        }
    ],
    "action_items": [
        {
            "task": "Practice evidence-checking when assuming others' thoughts",
            "category": "cognitive",
            "details": "When mind-reading: ask 'what's the evidence?' and 'what's another explanation?'"
        },
        {
            "task": "Try worry journaling at 3am wakings",
            "category": "behavioral",
            "details": "Box breathing first, then 5 min writing if mind still racing, then back to bed"
        }
    ],
    "session_mood": "low",
    "mood_trajectory": "improving"
}
