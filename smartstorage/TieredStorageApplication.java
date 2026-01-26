package com.example.tieredstorage;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class TieredStorageApplication {

    public static void main(String[] args) {
        SpringApplication.run(TieredStorageApplication.class, args);
        System.out.println("Smart Tiered Storage is running...");
    }
}