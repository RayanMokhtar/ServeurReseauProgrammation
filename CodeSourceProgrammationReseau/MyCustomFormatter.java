import java.io.*;
import java.net.SocketException;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.util.Scanner;
import java.util.logging.Logger;
import java.util.logging.Level;
import java.util.logging.FileHandler;
import java.util.logging.SimpleFormatter;
import java.util.logging.Formatter;
import java.util.logging.LogRecord;

public class MyCustomFormatter extends Formatter {
    @Override
    public String format(LogRecord record) {
        // Retourner uniquement le message du log
        return record.getMessage() + "\n";
    }
}