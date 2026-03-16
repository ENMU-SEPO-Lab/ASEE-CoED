import java.util.Scanner;

/**
 * @author Ludwig.Scherer
 * This program converts shorthand card notation into full card descriptions.
 */
public class CardDescription {

    // Valid ranks and suits
    private static final String[] VALID_RANKS = 
        {"A","2","3","4","5","6","7","8","9","10","J","Q","K"};
    private static final String[] VALID_SUITS = {"D","H","S","C"};

    /**
     * Checks if the input is a valid rank.
     */
    public static boolean isValidRank(String rank) {
        for (String r : VALID_RANKS) {
            if (r.equalsIgnoreCase(rank)) return true;
        }
        return false;
    }

    /**
     * Checks if the input is a valid suit.
     */
    public static boolean isValidSuit(String suit) {
        for (String s : VALID_SUITS) {
            if (s.equalsIgnoreCase(suit)) return true;
        }
        return false;
    }

    /**
     * Converts shorthand rank and suit into a full card description.
     * @param rank The shorthand rank (A, 2-10, J, Q, K)
     * @param suit The shorthand suit (D, H, S, C)
     * @return The full description of the card or an error message
     */
    public static String getCardDescription(String rank, String suit) {

        // First check invalid inputs
        if (!isValidRank(rank)) return "Invalid rank input.";
        if (!isValidSuit(suit)) return "Invalid suit input.";

        // Map rank
        String fullRank;
        switch (rank.toUpperCase()) {
            case "A": fullRank = "Ace"; break;
            case "J": fullRank = "Jack"; break;
            case "Q": fullRank = "Queen"; break;
            case "K": fullRank = "King"; break;
            default: fullRank = rank; // numbers 2-10
        }

        // Map suit
        String fullSuit;
        switch (suit.toUpperCase()) {
            case "D": fullSuit = "Diamonds"; break;
            case "H": fullSuit = "Hearts"; break;
            case "S": fullSuit = "Spades"; break;
            case "C": fullSuit = "Clubs"; break;
            default: fullSuit = "Invalid suit input."; // shouldn't happen
        }

        return fullRank + " of " + fullSuit;
    }

    /**
     * Main method that gets user input and prints the full card description.
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

