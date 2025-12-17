import java.util.Scanner;

/**
 * @author Essa Imhmed
 * Due date: 2/27/2025
 * This program converts shorthand card notation into full card descriptions.
 */
public class CardDescription {
    /**
     * Converts shorthand rank and suit into a full card description.
     * If either input is invalid, returns an error message.
     * @param rank The shorthand rank (A, 2-10, J, Q, K)
     * @param suit The shorthand suit (D, H, S, C)
     * @return The full description of the card or an error message
     */
    public static String getCardDescription(String rank, String suit) {
        String fullRank = switch (rank.toUpperCase()) {
            case "A" -> "Ace";
            case "J" -> "Jack";
            case "Q" -> "Queen";
            case "K" -> "King";
            case "2", "3", "4", "5", "6", "7", "8", "9", "10" -> rank;
            default -> "Invalid rank input.";
        };
        String fullSuit = switch (suit.toUpperCase()) {
            case "D" -> "Diamonds";
            case "H" -> "Hearts";
            case "S" -> "Spades";
            case "C" -> "Clubs";
            default -> "Invalid suit input.";
        };
        if (fullRank.startsWith("Invalid") || fullSuit.startsWith("Invalid")) {
            return fullRank.startsWith("Invalid") ? fullRank : fullSuit;
        }
        return fullRank + " of " + fullSuit;
    }
    /**
     * Main method that gets user input and prints the full card description.
     * @param args Command-line arguments
     */
    public static void main(String[] args) {
        try (Scanner scanner = new Scanner(System.in)) {
            System.out.print("Enter the rank of the card: ");
            String rank = scanner.nextLine();

            System.out.print("Enter the suit of the card: ");
            String suit = scanner.nextLine();

            String description = getCardDescription(rank, suit);
            System.out.println("Card description: " + description);
        }
    }
}