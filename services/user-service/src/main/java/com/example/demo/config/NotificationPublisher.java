//package com.example.demo.config;
//
//import com.example.demo.dto.NotificationRequestDTO;
//import org.springframework.stereotype.Component;
//
//@Component
//public class NotificationPublisher {
//
//    public void publish(String exchange, String routingKey, Object message) {
//        System.out.println("Publishing message: " + message + " to exchange: " + exchange);
//    }
//}

package com.example.demo.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;

@Component
public class NotificationPublisher {

    private final RabbitTemplate rabbitTemplate;
    private final ObjectMapper objectMapper;

    public NotificationPublisher(RabbitTemplate rabbitTemplate, ObjectMapper objectMapper) {
        this.rabbitTemplate = rabbitTemplate;
        this.objectMapper = objectMapper;
    }

    public void publish(String exchange, String routingKey, Object message) {
        try {
            String json = objectMapper.writeValueAsString(message);
            rabbitTemplate.convertAndSend(exchange, routingKey, json);
            System.out.println("Message published to RabbitMQ: " + json);
        } catch (Exception e) {
            System.err.println("Failed to publish message: " + e.getMessage());
            throw new RuntimeException(e);
        }
    }
}


