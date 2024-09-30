def tokenize_kannada_text(text, preserve_spaces=False):
    """
    Splits Kannada text into tokens based on syllable patterns.
    """

    # Define character classes based on Unicode categories
    C = r'[\u0C80-\u0C96\u0C98-\u0CBF\u0CC0-\u0CC4\u0CC7\u0CC8\u0CCA\u0CCB\u0CCD-\u0CD5\u0CD6-\u0CDF]'  # Consonants
    V = r'[\u0C85-\u0C94\u0C9E-\u0CA8\u0CAE-\u0CB9\u0CBF]'  # Vowels
    Ra = r'\u0CB0'  # Repha
    H = r'\u0CCD'  # Halant
    ZWNJ = r'\u200C'  # Zero Width Non-Joiner
    ZWJ = r'\u200D'  # Zero Width Joiner
    N = r'\u0C82\u0C83'  # Nukta
    A = r'\u0C80'  # Avagraha
    M = r'[\u0CBA\u0CBB\u0CBC]'  # Modifiers (Candrabindu, Anusvara, Visarga)
    SM = r'[\u0CBE\u0CBF\u0CC0-\u0CC4\u0CC6-\u0CC8\u0CCA\u0CCB\u0CCC\u0CCD]'  # Sign/Modifier
    VD = r''  # Vedic Tone Marks (not included in this example)
    NBSP = r'\u00A0'  # Non-Breaking Space

    # Define syllable patterns
    consonant_syllable_pattern = rf"""
        ({C}+{N}*<{H}+(<{ZWNJ}|{ZWJ}>)*|(<{ZWNJ}|{ZWJ}>)+{H}>) +  {C}+{N}*[{A}] + [< {H}+(<{ZWNJ}|{ZWJ}>)* | ({M}+{N}*){H}>]+ {SM}*[{VD}]
    """
    vowel_syllable_pattern = rf"""
        ([{Ra}]+{H})?{V}+{N}* + 
        [<(<{ZWJ}|{ZWNJ}>)+{H}+{C}|{ZWJ}+{C}>]+
        ({M}+{N}*[{H}])*{SM}*[{VD}]
    """
    stand_alone_cluster_pattern = rf"""
        ([{Ra}]+{H})?{NBSP}+{N}* + 
        [<(<{ZWJ}|{ZWNJ}>)+{H}+{C}|{ZWJ}+{C}>]+
        ({M}+{N}*[{H}])*{SM}*[{VD}]
    """

    # Combine patterns and find all matches
    combined_pattern = f"({consonant_syllable_pattern})|({vowel_syllable_pattern})|({stand_alone_cluster_pattern})"
    matches = re.finditer(combined_pattern, text, re.VERBOSE | re.UNICODE)

    # Extract tokens from matches
    tokens = [match.group(0) for match in matches]

    # Handle whitespace if not preserved
    if not preserve_spaces:
        tokens = [token.strip() for token in tokens]

    return tokens