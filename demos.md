## Creating Indexes

- Create indexes with different embedding functions. 
- CPU and CUDA mode supported through SentenceTransformers library. 
- OpenAI embeddings are also avilable.

[creating indexes](https://github.com/blob42/Instrukt/assets/210457/e50c214b-88e9-4792-87b0-6a1b68253767)


## Use indxes and tools with agents

- Attach indexes and tools to agents on the fly.
- Use them for doing Retrieval Augmented Generation (RAG).

[using indexes and tools with agents](https://github.com/blob42/Instrukt/assets/210457/86e498f9-deb2-4bba-9f39-f1efafeb581e)


## Fuzzy select sources and edit messages

- Use `ctrl+p` to select and edit source documents used for retrieval Q&A.
Selection is sent as stdin to the program exported in `$SELECTOR`

- Use `ctrl+e` to edit the agent reply or input using an external `$EDITOR`.


[fuzzy select and
edit](https://github.com/blob42/Instrukt/assets/210457/583eb8d6-57b3-4f7d-9ad2-830e5ff97258)



