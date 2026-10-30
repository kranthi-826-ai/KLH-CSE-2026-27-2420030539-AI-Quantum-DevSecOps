package com.pqc.security.crypto.hybrid;

import java.nio.ByteBuffer;
import java.security.GeneralSecurityException;

final class BinaryComponents {
    private BinaryComponents() { }

    static byte[] join(byte[] first, byte[] second) {
        return ByteBuffer.allocate(Integer.BYTES + first.length + second.length)
                .putInt(first.length).put(first).put(second).array();
    }

    static byte[][] split(byte[] encoded) throws GeneralSecurityException {
        if (encoded == null || encoded.length < Integer.BYTES) {
            throw new GeneralSecurityException("Invalid hybrid component encoding");
        }
        ByteBuffer buffer = ByteBuffer.wrap(encoded);
        int firstLength = buffer.getInt();
        if (firstLength <= 0 || firstLength > buffer.remaining()) {
            throw new GeneralSecurityException("Invalid hybrid component length");
        }
        byte[] first = new byte[firstLength];
        byte[] second = new byte[buffer.remaining() - firstLength];
        buffer.get(first).get(second);
        if (second.length == 0) throw new GeneralSecurityException("Missing hybrid component");
        return new byte[][] { first, second };
    }
}
