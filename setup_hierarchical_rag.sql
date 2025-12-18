-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- 1. Create the Parent Table (Stores the full section content)
-- This table holds the larger context that will be returned to the LLM.
create table if not exists sakhi_sections (
  id bigserial primary key,
  header_path text, -- e.g., "Male Fertility > Causes"
  content text,     -- The full text of the section
  token_count int
);

-- 2. Create the Child Table (Stores vectors for search)
-- This table holds smaller chunks of text and their embeddings for efficient similarity search.
create table if not exists sakhi_section_chunks (
  id bigserial primary key,
  section_id bigint references sakhi_sections(id) on delete cascade,
  chunk_content text, -- The small snippet used for matching
  embedding vector(1536) -- OpenAI text-embedding-3-small dimensions
);

-- 3. Create a function to search children but return PARENT content
-- This RPC function performs the "magic" of searching small chunks but returning the full parent context.
create or replace function hierarchical_search (
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
returns table (
  section_content text,
  header_path text,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select distinct on (sakhi_sections.id)
    sakhi_sections.content,
    sakhi_sections.header_path,
    1 - (sakhi_section_chunks.embedding <=> query_embedding) as similarity
  from sakhi_section_chunks
  join sakhi_sections on sakhi_sections.id = sakhi_section_chunks.section_id
  where 1 - (sakhi_section_chunks.embedding <=> query_embedding) > match_threshold
  order by sakhi_sections.id, similarity desc
  limit match_count;
end;
$$;
