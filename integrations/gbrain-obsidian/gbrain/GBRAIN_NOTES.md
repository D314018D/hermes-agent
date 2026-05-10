# GBrain integration notes

Recommended sequence:

1. Treat `obsidian-vault/` as the brain repo during MVP.
2. Run local ingestion into Markdown first.
3. Enable GBrain after Markdown quality is stable.
4. Use PGLite/local mode first; migrate to Postgres/Supabase only after the brain grows.
5. Run maintenance/dream jobs after ingestion quality is acceptable.

Important:
- The Markdown note is the durable source.
- GBrain index/graph can be rebuilt.
- Do not put raw junk into the vault.
