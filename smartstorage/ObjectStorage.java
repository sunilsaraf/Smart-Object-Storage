package com.example.tieredstorage.storage;

import java.io.File;
import java.io.IOException;

public interface ObjectStorage {
    void putObject(String objectId, byte[] data) throws IOException;
    byte[] getObject(String objectId) throws IOException;
    void deleteObject(String objectId) throws IOException;
    File exportObject(String objectId) throws IOException;
}