-- Update match_faq to include infographic_url and follow_up_questions

create or replace function match_faq (
  query_embedding vector(1536),
  match_count int
)
returns table (
  id int,
  question text,
  answer text,
  youtube_link text,
  infographic_url text,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    sakhi_faq.id,
    sakhi_faq.question,
    sakhi_faq.answer,
    sakhi_faq.youtube_link,
    sakhi_faq.infographic_url,
    1 - (sakhi_faq.question_vector <=> query_embedding) as similarity
  from sakhi_faq
  where 1 - (sakhi_faq.question_vector <=> query_embedding) > 0.5 -- Threshold
  order by similarity desc
  limit match_count;
end;
$$;
