import { Pagination, PaginationContent, PaginationEllipsis, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from "../ui/pagination";

interface PageSelectProps {
    page: number
    total: number
    setPage: (page: number) => void
}

export function PageSelectPN({ page, total, setPage }: PageSelectProps) {
    const paginationContent: React.JSX.Element[] = [];
    if (total !== null) {
        if (page > 1) {
            paginationContent.push(
                <PaginationItem key="prev">
                    <PaginationPrevious onClick={() => setPage(page - 1)} />
                </PaginationItem>
            );
            paginationContent.push(
                <PaginationItem key={1}>
                    <PaginationLink onClick={() => setPage(1)}>{1}</PaginationLink>
                </PaginationItem>
            );
            if (page > 2) {
                paginationContent.push(
                    <PaginationItem key="dot-before">
                        <PaginationEllipsis />
                    </PaginationItem>
                );
            }
        }
        paginationContent.push(
            <PaginationItem key={page}>
                <PaginationLink isActive>{page}</PaginationLink>
            </PaginationItem>
        );
        if (total > page) {
            if (total > page + 1) {
                paginationContent.push(
                    <PaginationItem key="dot-after">
                        <PaginationEllipsis />
                    </PaginationItem>
                );
            }
            paginationContent.push(
                <PaginationItem key={total}>
                    <PaginationLink onClick={() => setPage(total)}>{total}</PaginationLink>
                </PaginationItem>
            );
            paginationContent.push(
                <PaginationItem key="next">
                    <PaginationNext onClick={() => setPage(page + 1)} />
                </PaginationItem>
            );
        }
    }
    return (
        <Pagination>
            <PaginationContent>
                {paginationContent}
            </PaginationContent>
        </Pagination>
    );
}

export function PageSelectNum({ page, total, setPage }: PageSelectProps) {
    const paginationContent: React.JSX.Element[] = [];
    if (total) {
        if (page > 2) {
            paginationContent.push(
                <PaginationItem key={1}>
                    <PaginationLink onClick={() => setPage(1)}>{1}</PaginationLink>
                </PaginationItem>
            );
        }
        if (page > 3) {
            if (page === 4) {
                paginationContent.push(
                    <PaginationItem key={2}>
                        <PaginationLink onClick={() => setPage(2)}>{2}</PaginationLink>
                    </PaginationItem>
                );
            } else {
                paginationContent.push(
                    <PaginationItem key="dot-before">
                        <PaginationEllipsis />
                    </PaginationItem>
                );
            }
        }
        if (page > 1) {
            paginationContent.push(
                <PaginationItem key={page - 1}>
                    <PaginationLink onClick={() => setPage(page - 1)}>{page - 1}</PaginationLink>
                </PaginationItem>
            );
        }
    }
    paginationContent.push(
        <PaginationItem key={page}>
            <PaginationLink isActive>{page}</PaginationLink>
        </PaginationItem>
    );
    if (total) {
        if (total > page) {
            paginationContent.push(
                <PaginationItem key={page + 1}>
                    <PaginationLink onClick={() => setPage(page + 1)}>{page + 1}</PaginationLink>
                </PaginationItem>
            );
        }
        if (total > page + 2) {
            if (page === total - 3) {
                paginationContent.push(
                    <PaginationItem key={total - 1}>
                        <PaginationLink onClick={() => setPage(total - 1)}>{total - 1}</PaginationLink>
                    </PaginationItem>
                );
            } else {
                paginationContent.push(
                    <PaginationItem key="dot-after">
                        <PaginationEllipsis />
                    </PaginationItem>
                );
            }
        }
        if (total > page + 1) {
            paginationContent.push(
                <PaginationItem key={total}>
                    <PaginationLink onClick={() => setPage(total)}>{total}</PaginationLink>
                </PaginationItem>
            );
        }
    }
    return (
        <Pagination>
            <PaginationContent>
                {paginationContent}
            </PaginationContent>
        </Pagination>
    );
}