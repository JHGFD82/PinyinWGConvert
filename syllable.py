class Syllable:
    """
    Class representing a syllable with its initial, final, and validation status.
    """

    def __init__(self, initial: str, final: str, init_list: list, fin_list: list, ar: list):
        """
        Initializes a Syllable instance.

        Parameters:
            initial (str): The initial part of the syllable.
            final (str): The final part of the syllable.
            init_list (list): List of valid initials.
            fin_list (list): List of valid finals.
            ar (list): Array representing valid initial-final combinations.
        """
        self.initial = initial
        self.final = final
        self.full_syl = self.compose_full_syllable(initial, final)
        self.length = len(self.full_syl)
        self.valid = self.validate_syllable(init_list, fin_list, ar)

    def compose_full_syllable(self, initial: str, final: str) -> str:
        """
        Composes the full syllable from its initial and final parts.

        Parameters:
            initial (str): The initial part of the syllable.
            final (str): The final part of the syllable.

        Returns:
            str: The full syllable.
        """
        if initial == 'ø':
            return final
        return initial + final

    def validate_syllable(self, init_list: list, fin_list: list, ar: list) -> bool:
        """
        Validates the syllable based on the initial and final lists and the array.

        Parameters:
            init_list (list): List of valid initials.
            fin_list (list): List of valid finals.
            ar (list): Array representing valid initial-final combinations.

        Returns:
            bool: True if the syllable is valid, False otherwise.
        """
        try:
            init_index = init_list.index(self.initial)
            fin_index = fin_list.index(self.final)
            return ar[init_index][fin_index]
        except ValueError:
            return False

    def __str__(self):
        """
        String representation of the Syllable.

        Returns:
            str: String representation.
        """
        return f"Syllable('{self.full_syl}', Valid: {self.valid})"
