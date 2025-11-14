package com.example.demo.config;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.DirectExchange;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.amqp.core.Queue;



@Configuration
public class RabbitMQConfig {

    public static final String EXCHANGE = "notifications.direct";
    public static final String EMAIL_QUEUE = "email.queue";
    public static final String PUSH_QUEUE = "push.queue";

    @Bean
    public DirectExchange notificationExchange() {
        return new DirectExchange(EXCHANGE);
    }

    @Bean
    public Queue emailQueue() {
        return new Queue(EMAIL_QUEUE, true);
    }

    @Bean
    public Queue pushQueue() {
        return new Queue(PUSH_QUEUE, true);
    }

    @Bean
    public Binding emailBinding() {
        return BindingBuilder.bind(emailQueue())
                .to(notificationExchange())
                .with(EMAIL_QUEUE);
    }

    @Bean
    public Binding pushBinding() {
        return BindingBuilder.bind(pushQueue())
                .to(notificationExchange())
                .with(PUSH_QUEUE);
    }
}
