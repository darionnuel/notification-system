package com.example.demo.dto;

public class ApiResponse<T> {
    private boolean success;
    private T data;
    private String error;
    private String message;
    private PaginationMeta meta;

    public ApiResponse(boolean success, T data, String error, String message, PaginationMeta meta) {
        this.success = success;
        this.data = data;
        this.error = error;
        this.message = message;
        this.meta = meta;
    }

    public boolean isSuccess() { return success; }
    public void setSuccess(boolean success) { this.success = success; }

    public T getData() { return data; }
    public void setData(T data) { this.data = data; }

    public String getError() { return error; }
    public void setError(String error) { this.error = error; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }

    public PaginationMeta getMeta() { return meta; }
    public void setMeta(PaginationMeta meta) { this.meta = meta; }
}
