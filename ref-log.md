Reflection – Multi-Agent Trip Designer
Key Takeaways

This project gave me a deeper understanding of how multi-agent systems can mimic collaboration between distinct roles. Creating the Designer and Verifier agents felt like orchestrating two different personalities — one imaginative and expressive, the other methodical and precise. I learned how to craft prompts so that the Designer could produce engaging, story-like itineraries, while the Verifier acted as a practical fact-checker using the internet tool. Seeing the agents work together to generate more realistic and actionable travel plans than either could alone was incredibly insightful.

Challenges Encountered

Managing asynchronous behavior in Streamlit was the biggest technical hurdle. I had to implement a safe wrapper around asyncio.run() to prevent event loop conflicts. Another challenge was fine-tuning the prompts — initially, the Designer tended to over-explain or repeat ideas, and the Verifier came across as too strict. I adjusted their tone and focus so that one felt like a friendly travel storyteller and the other like a thoughtful, detail-oriented editor. I also enhanced the UI: making tool logs collapsible, adding progress indicators, and softening error messages improved the overall experience.

Creative Design Decisions

I gave the Designer a warm, narrative voice to make itineraries feel personal and engaging. The Verifier was designed to be analytical, almost like a travel editor ensuring accuracy and coherence. Together, their interplay balances creativity with practicality, making the workflow feel human rather than mechanical.

Tools and Support

I leveraged ChatGPT (GPT-5) to refine prompts, organize the multi-agent flow, and troubleshoot async issues. All creative direction, final design decisions, and implementation choices were made independently.