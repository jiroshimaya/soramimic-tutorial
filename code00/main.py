import editdistance as ed
import MeCab

def sort_by_distance(target_word: dict, wordlist: list[dict]) -> list[dict]:
    """
    対象単語の発音と単語リストの各単語の発音との編集距離に基づいて、単語リストをソートします。
    
    引数:
    target_word (dict): 編集距離の比較対象となる 'pronunciation' キーを含む辞書。
    wordlist (list of dict): 各々が少なくとも 'pronunciation' キーを含む辞書のリスト。
    
    戻り値:
    list of dict: 対象単語の発音に対する編集距離が増加する順にソートされた単語リスト。
    """
    # 発音に基づいて単語リストの各単語の編集距離を計算
    distances = [(word, calculate_distance(target_word, word)) for word in wordlist]
    # 編集距離（第二要素）に基づいてタプルのリストをソート
    sorted_distances = sorted(distances, key=lambda x: x[1])
    # タプルのリストからソートされた単語を抽出
    sorted_wordlist = [word for word, distance in sorted_distances]
    return sorted_wordlist

def calculate_distance(dict1: dict, dict2: dict) -> int:
    """
    2つの辞書から 'pronunciation' キーの値を取得し、その編集距離を計算して返します。

    引数:
    dict1 (dict): 'pronunciation' キーを含む辞書。
    dict2 (dict): 'pronunciation' キーを含む辞書。

    戻り値:
    int: 2つの発音の編集距離。
    """
    return ed.eval(dict1['pronunciation'], dict2['pronunciation'])



class PhraseTokenizer:
    def __init__(self):
        self.m = MeCab.Tagger('')  # MeCabのタグ付けオブジェクトを宣言

    def tokenize(self, text: str) -> list[dict]:
        """
        テキストをトークン化し、各トークンの詳細情報を含む辞書のリストを返します。
        
        引数:
        text (str): トークン化するテキスト
        
        戻り値:
        list[dict]: トークンの詳細情報を含む辞書のリスト
        """
        mecab_result = self.m.parse(text).splitlines()
        mecab_result = mecab_result[:-1]  # 最後の行は不要なので削除
        tokens = []
        word_id = 509800  # 単語のIDの開始番号
        for line in mecab_result:
            if '\t' not in line:
                continue
            parts = line.split('\t')
            word_surface = parts[0]  # 単語の表層形
            pos_info = parts[1].split(',')  # 品詞やその他の文法情報
            token = {
                'surface_form': word_surface,
                'pos': pos_info[0],
                'pos_detail_1': pos_info[1] if len(pos_info) > 1 else '*',
                'pos_detail_2': pos_info[2] if len(pos_info) > 2 else '*',
                'pos_detail_3': pos_info[3] if len(pos_info) > 3 else '*',
                'conjugated_type': pos_info[4] if len(pos_info) > 4 else '*',
                'conjugated_form': pos_info[5] if len(pos_info) > 5 else '*',
                'basic_form': pos_info[6] if len(pos_info) > 6 else word_surface,
                'reading': pos_info[7] if len(pos_info) > 7 else '',
                'pronunciation': pos_info[8] if len(pos_info) > 8 else ''
            }
            tokens.append(token)
        return tokens

    def split_text_into_phrases(self, text: str, consider_non_independent_nouns_as_breaks: bool = True) -> list[dict]:
        """
        テキストをフレーズに分割し、各フレーズの詳細情報を含む辞書のリストを返します。
        
        引数:
        text (str): フレーズに分割するテキスト
        
        戻り値:
        list[dict]: フレーズの詳細情報を含む辞書のリスト
        """
        tokens = self.tokenize(text)
        phrase_break_pos_tags = ['名詞', '動詞', '接頭詞', '副詞', '感動詞', '形容詞', '形容動詞', '連体詞']  # フレーズを区切る品詞のリスト
        segmented_text = []  # 分割されたテキストのリスト
        current_phrase = {'surface': '', 'pronunciation': ''}

        previous_token = None

        for token in tokens:
            word_surface = token['surface_form']
            word_pronunciation = token['pronunciation']
            pos_info = token['pos']
            pos_detail = ','.join([token['pos_detail_1'], token['pos_detail_2'], token['pos_detail_3']])

            # 現在の単語がフレーズを区切るか判断
            should_break = pos_info in phrase_break_pos_tags
            if not consider_non_independent_nouns_as_breaks:
                should_break = should_break and '接尾' not in pos_detail
                should_break = should_break and not (pos_info == '動詞' and 'サ変接続' in pos_detail)
                should_break = should_break and '非自立' not in pos_detail
                if previous_token:
                    previous_pos_info = previous_token['pos']
                    previous_pos_detail = ','.join([previous_token['pos_detail_1'], previous_token['pos_detail_2'], previous_token['pos_detail_3']])
                    should_break = should_break and previous_pos_info != '接頭詞'
                    should_break = should_break and not ('サ変接続' in previous_pos_detail and pos_info == '動詞' and token['conjugated_type'] == 'サ変・スル')

            if should_break:
                if current_phrase['surface']:
                    segmented_text.append(current_phrase)
                current_phrase = {'surface': '', 'pronunciation': ''}
            current_phrase['surface'] += word_surface
            current_phrase['pronunciation'] += word_pronunciation

            previous_token = token

        if current_phrase['surface']:  # 存在する場合は最後のフレーズを追加
            segmented_text.append(current_phrase)
        return segmented_text
    def get_pronunciation(self, text: str) -> str:
        """
        テキストの発音を取得します。
        
        引数:
        text (str): 発音を取得するテキスト
        
        戻り値:
        str: テキストの発音
        """
        tokens = self.tokenize(text)
        pronunciation = ''.join(token['pronunciation'] for token in tokens if token['pronunciation'])
        return pronunciation

def load_wordlist(filepath: str) -> list[dict]:
    """
    ファイルパスから単語リストを読み込み、各単語の詳細情報を含む辞書のリストを返します。
    
    引数:
    filepath (str): 単語リストが格納されているファイルのパス
    
    戻り値:
    list[dict]: 単語の詳細情報を含む辞書のリスト
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.read().splitlines()
        wordlist = []
        tokenizer = PhraseTokenizer()
        for id, line in enumerate(lines):
            wordlist.append({
                'id': id,
                'surface': line,
                'pronunciation': tokenizer.get_pronunciation(line)
            })
        return wordlist


def find_closest_words(text: str, wordlist: list[dict]) -> list[dict]:
    """
    分割されたフレーズごとに、単語リストの中から発音の編集距離が最も近い単語を見つけて辞書のリストとして返します。

    引数:
    text (str): 入力テキスト
    wordlist (list[dict]): 単語リスト、各単語は辞書形式で 'surface' と 'pronunciation' キーを持つ

    戻り値:
    list[dict]: 各フレーズに最も近い単語の辞書のリスト
    """
    tokenizer = PhraseTokenizer()
    phrases = tokenizer.split_text_into_phrases(text)
    closest_words = []

    for phrase in phrases:
        sorted_words = sort_by_distance(phrase, wordlist)
        closest_word = {
          "closest_word": sorted_words[0],
          "original_phrase": phrase    
        }

        closest_words.append(closest_word)

    return closest_words


if __name__ == "__main__":
    wordlist = load_wordlist("sample_wordlist.csv")
    original_text = "海は広いな大きいな。月がのぼるし日が沈む"
    closest_words = find_closest_words(original_text, wordlist)
    
    for word in closest_words:
        print(word["original_phrase"]["pronunciation"], word["closest_word"]["pronunciation"])
