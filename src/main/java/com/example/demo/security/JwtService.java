package com.example.demo.security;

import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.SignatureAlgorithm;
import org.springframework.stereotype.Component;

import java.security.Key;

@Component
public class JwtService {
    private Key key = Keys.secretKeyFor(SignatureAlgorithm.HS256); // generates a 256-bit key

    public String generateToken(String subject) {
        return io.jsonwebtoken.Jwts.builder()
                .setSubject(subject)
                .signWith(key)
                .compact();
    }
}
