package com.example.demo.config;

import com.example.demo.dto.NotificationRequestDTO;
import org.springframework.stereotype.Component;

@Component
public class NotificationPublisher {

    public void publish(String exchange, String routingKey, Object message) {
        // Placeholder method — will later send message to RabbitMQ
        System.out.println("Publishing message: " + message + " to exchange: " + exchange);
    }
}

