

def LPS(pattern):
    m = len(pattern)
    lps = [0] * m
    j = 0
    i = 1

    while i < m:
        if pattern[i] == pattern[j]:
            j += 1
            lps[i] = j
            i += 1
        else:
            if j != 0:
                j = lps[j - 1]
            else:
                lps[i] = 0
                i += 1
    
    return lps

def KMP(text, pattern):
    n = len(text)
    m = len(pattern)
    lps = LPS(pattern)
    i = 0
    j = 0
    indexes = []

    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1
        
        if j == m:
            indexes.append(i - j)
            j = lps[j - 1]
        elif i < n and pattern[j] != text[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return indexes

pattern = '10'
string = '101100'

KMP_indexes = KMP(string, pattern)
print(f"Pattern '{pattern}' found at indexes: {KMP_indexes}")



