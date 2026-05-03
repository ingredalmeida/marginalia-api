import { PAGE_SIZE } from '@/lib/pagination';
import { fetchAuthorsPage } from '@/services/authorApi';
import type { AuthorRead } from '@/services/bookApi';

/** Carrega todos os autores para selects admin (paginação interna). */
export async function fetchAllAuthors(token: string): Promise<AuthorRead[]> {
  const acc: AuthorRead[] = [];
  let p = 1;
  while (true) {
    const page = await fetchAuthorsPage(token, { page: p, page_size: PAGE_SIZE });
    acc.push(...page.items);
    if (p >= page.pages) break;
    p += 1;
  }
  return acc;
}
