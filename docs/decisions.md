# decisions.md

File where I explain some of my choices that I made

## tech stack / framework choices

### fastapi

In terms of building API's I'm very familiar with Python, Ruby, and C#.
FastAPI is something we've been using at work and I quite like it.
I like using Pydantic when working with data models in Python, and FastAPI integrates very well with Pydantic.

### claude code

The AI coding agent I'm most familiar with.
I find using Opus 5.5 is sufficient for most of my coding tasks.
I have some plugins like Ponytail that I find very useful.

## code choices

### modeling

I broke down the models pretty much verbatim from the JSON file input.
I decided to make almost all of the fields on the models optional, just to keep the system very flexible. In a real 
production environment I would base my decisions off of actual data requirements / expectations.
I did make `resourceType` and `id` required though, as my in-memory store for it relies on those 2 fields being set.

### read_resource endpoint

I'm going to be completely honest, Claude wrote up that endpoint, but I kinda dig it to be honest.
In an actual production API I'd create concrete GET endpoints for specific resources I'd want the API to be able to 
respond with.
However, for the use case of this example API I think it actually quite clever. If there is a new data set that is fed 
to the code with new resource types, then the GET endpoint will dynamically allow the consumer to fetch those resources 
without having to write new code for it.

### why no CRUD endpoints?

In the prompt, it states:
> "Build an API that makes this data useful and queryable. Before you start, think carefully about who is consuming 
> this API and what they actually need from it."

From my perspective, the data didn't seem like something we'd want to be building a REST API around. I figured this API 
would mainly focus on pulling down data, and giving the user the ability to query useful sets of information.

I imagined this API would sit in front of another API that would allow for direct database access and manipulation. 
Maybe a GraphQL API or a REST API that interfaces directly with the database. Over there a proper file injestion system 
could live.

Perhaps this API is externally faced (maybe an API specifically for life science partners?) and so this API separates 
the data source from fetching data sets. Perhaps the FHIR resources data set is coming from an external source, in 
which case it wouldn't be appropriate for the user to have the ability to edit the data.
