package com.example.demo.dto;

public class PaginationMeta {
    private long total;
    private int limit;
    private int page;
    private long total_pages;
    private boolean has_next;
    private boolean has_previous;

    public PaginationMeta() {}

    public PaginationMeta(long total, int limit, int page, long total_pages, boolean has_next, boolean has_previous) {
        this.total = total;
        this.limit = limit;
        this.page = page;
        this.total_pages = total_pages;
        this.has_next = has_next;
        this.has_previous = has_previous;
    }

    public long getTotal() { return total; }
    public void setTotal(long total) { this.total = total; }

    public int getLimit() { return limit; }
    public void setLimit(int limit) { this.limit = limit; }

    public int getPage() { return page; }
    public void setPage(int page) { this.page = page; }

    public long getTotal_pages() { return total_pages; }
    public void setTotal_pages(long total_pages) { this.total_pages = total_pages; }

    public boolean isHas_next() { return has_next; }
    public void setHas_next(boolean has_next) { this.has_next = has_next; }

    public boolean isHas_previous() { return has_previous; }
    public void setHas_previous(boolean has_previous) { this.has_previous = has_previous; }
}
