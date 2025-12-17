
import org.junit.*;
import java.util.Scanner;


public class TestCardDescription {

    CardDescription cardDescription;

    @Before
    public void setUp() {
        cardDescription = new CardDescription();
    }

    @Test
    public void testGetCardDescription_AceOfDiamonds() {
        // Given
        String rank = "A";
        String suit = "D";

        // When
        String cardDescriptionResult = cardDescription.getCardDescription(rank, suit);

        // Then
        Assert.assertEquals("Ace of Diamonds", cardDescriptionResult);
    }

    @Test
    public void testGetCardDescription_KingOfSpades() {
        // Given
        String rank = "K";
        String suit = "S";

        // When
        String cardDescriptionResult = cardDescription.getCardDescription(rank, suit);

        // Then
        Assert.assertEquals("King of Spades", cardDescriptionResult);
    }

    @Test
    public void testGetCardDescription_QueenOfHearts() {
        // Given
        String rank = "Q";
        String suit = "H";

        // When
        String cardDescriptionResult = cardDescription.getCardDescription(rank, suit);

        // Then
        Assert.assertEquals("Queen of Hearts", cardDescriptionResult);
    }

    @Test
    public void testGetCardDescription_JackOfClubs() {
        // Given
        String rank = "J";
        String suit = "C";

        // When
        String cardDescriptionResult = cardDescription.getCardDescription(rank, suit);

        // Then
        Assert.assertEquals("Jack of Clubs", cardDescriptionResult);
    }

    @Test
    public void testGetCardDescription_FiveOfDiamonds() {
        // Given
        String rank = "5";
        String suit = "D";

        // When
        String cardDescriptionResult = cardDescription.getCardDescription(rank, suit);

        // Then
        Assert.assertEquals("Five of Diamonds", cardDescriptionResult);
    }

    @Test
    public void testGetCardDescription_InvalidRank() {
        // Given
        String rank = "X";
        String suit = "D";

        // When
        String cardDescriptionResult = cardDescription.getCardDescription(rank, suit);

        // Then
        Assert.assertEquals("Invalid card rank", cardDescriptionResult);
    }

    @Test
    public void testGetCardDescription_InvalidSuit() {
        // Given
        String rank = "A";
        String suit = "Z";

        // When
        String cardDescriptionResult = cardDescription.getCardDescription(rank, suit);

        // Then
        Assert.assertEquals("Invalid card suit", cardDescriptionResult);
    }

    @Test
    public void testGetCardDescription_NullRank() {
        // Given
        String rank = null;
        String suit = "D";

        // When (should throw NullPointerException)
        try {
            cardDescription.getCardDescription(rank, suit);
            Assert.fail("Expected NullPointerException");
        } catch (NullPointerException e) {
            // Expected behavior
        }
    }

    @Test
    public void testGetCardDescription_NullSuit() {
        // Given
        String rank = "A";
        String suit = null;

        // When (should throw NullPointerException)
        try {
            cardDescription.getCardDescription(rank, suit);
            Assert.fail("Expected NullPointerException");
        } catch (NullPointerException e) {
            // Expected behavior
        }
    }

    @Test
    public void testGetCardDescription_EmptyRank() {
        // Given
        String rank = "";
        String suit = "D";

        // When (should return default description)
        String cardDescriptionResult = cardDescription.getCardDescription(rank, suit);

        // Then
        Assert.assertEquals("Invalid card rank", cardDescriptionResult);
    }

    @Test
    public void testGetCardDescription_EmptySuit() {
        // Given
        String rank = "A";
        String suit = "";

        // When (should return default description)
        String cardDescriptionResult = cardDescription.getCardDescription(rank, suit);

        // Then
        Assert.assertEquals("Invalid card suit", cardDescriptionResult);
    }
}
