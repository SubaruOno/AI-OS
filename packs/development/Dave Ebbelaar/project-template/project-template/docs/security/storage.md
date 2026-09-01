# Files and uploads

Supabase Storage holds files: photos, PDFs, spreadsheets, anything your app takes in or hands out. It has the same shape as the database, so the same thinking applies.

## Buckets stay private

A bucket is a folder. New buckets are private. Keep them that way.

A public bucket serves every file in it to anyone who knows or guesses its address. There is no sign-in, no rate limit, and no record of who downloaded what. `scripts/check-rls.sh` reports a public bucket as a finding, not a warning.

Create one through the dashboard, or in a migration:

```sql
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'documents',
  'documents',
  false,
  10485760,                                   -- 10 MB
  array['application/pdf', 'image/png', 'image/jpeg']
);
```

Always set `file_size_limit` and `allowed_mime_types`. A bucket with no size limit is a billing problem rather than a security one, and it is the failure small businesses actually hit.

## Handing out a file

To let someone download from a private bucket, generate a link that works for a few minutes:

```ts
const { data } = await supabase.storage
  .from("documents")
  .createSignedUrl(path, 60 * 5);   // valid for five minutes
```

The link carries its own permission and then expires. This is how a private bucket serves files without becoming public.

## Who can upload what

Storage files live in a normal table called `storage.objects`, so they follow the same rules as everything else.

**Levels 1 and 3** need no rules. Your server holds the secret key and works on behalf of whoever is signed in to your app.

**Level 2** gives each person their own folder, named after their account id:

```sql
create policy "uploads_own_folder" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "read_own_folder" on storage.objects
  for select to authenticated
  using (
    bucket_id = 'documents'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );
```

A file then lives at `documents/<account-id>/invoice-2026-01.pdf`, and the first part of that path is what the rule checks.

Add `update` and `delete` policies with the same condition when people need to replace or remove their own files.

## Checking uploads

An upload is data arriving from outside, so treat it that way:

- Check the file type on the server, not only in the browser. The browser check is for the person's benefit; the server check is for yours.
- Keep the size limit on the bucket, so a bad upload is refused before it costs anything.
- Store the original filename as data, and generate your own path. A filename is user input and can contain anything.

## Proving it works

The two-account test in [`rls.md`](rls.md), with a file instead of a row: upload as one account, note the path, then try to read that path as the second. A refusal is the pass.
