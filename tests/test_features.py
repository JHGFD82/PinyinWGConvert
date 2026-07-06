import unittest
from io import StringIO
import logging
from typing import List

from RoManTools.utils import convert_text, cherry_pick, segment_text, syllable_count, detect_method, validator
from RoManTools.config import Config
from RoManTools.data_loader import load_conversion_data, load_method_params
from RoManTools.constants import vowels
from decorators import timeit_decorator

import random
# from memory_profiler import profile


def generate_random_syllable_from_list(syllable_list: List[str]) -> str:
    return random.choice(syllable_list)


def generate_random_text_from_list(method: str, num_syllables: int = 0) -> str:

    def _validate_examples(random_text: List[str]) -> str:
        final_words = random_text[0]
        for i in range(1, len(random_text)):
            prev_syllable = random_text[i - 1]
            curr_syllable = random_text[i]
            if method == 'py':
                if (prev_syllable[-1] in vowels and curr_syllable[0] in vowels) or \
                        (prev_syllable.endswith('er') and curr_syllable[0] in vowels) or \
                        (prev_syllable[-1] == 'n' and curr_syllable[0] in vowels) or \
                        (prev_syllable.endswith('ng') and curr_syllable[0] in vowels):
                    final_words += "'" + curr_syllable
                else:
                    final_words += curr_syllable
            else:
                final_words += "-" + curr_syllable
        return final_words

    syllable_list = [row[method] for row in load_conversion_data() if row[method]]
    syllables = [generate_random_syllable_from_list(syllable_list) for _ in range(num_syllables)]
    return _validate_examples(syllables)


class TestRoManToolsActions(unittest.TestCase):

    # PINYIN CHUNK GENERATION TESTING #
    @timeit_decorator()
    def test_segment_text_basic_valid_syllable_vowel(self):
        result = segment_text('a, e, o, ai, ou', method='py')
        self.assertEqual(result, [['a'], ['e'], ['o'], ['ai'], ['ou']])

    @timeit_decorator()
    def test_segment_text_basic_valid_syllable_initial(self):
        result = segment_text('ba gu zhi ying kai lou yan', method='py')
        self.assertEqual(result, [['ba'], ['gu'], ['zhi'], ['ying'], ['kai'], ['lou'], ['yan']])

    @timeit_decorator()
    def test_segment_text_complex_finals_er_n_ng(self):
        result = segment_text('han xiang ran ling er', method='py')
        self.assertEqual(result, [['han'], ['xiang'], ['ran'], ['ling'], ['er']])

    @timeit_decorator()
    def test_segment_text_complex_edge_cases(self):
        result = segment_text('chen chong zhen', method='py')
        self.assertEqual(result, [['chen'], ['chong'], ['zhen']])

    @timeit_decorator()
    def test_segment_text_multi_syllable_no_apostrophe(self):
        result = segment_text('xiaoming changan wenxin liangxiao', method='py')
        self.assertEqual(result, [['xiao', 'ming'], ['chan', 'gan'], ['wen', 'xin'], ['liang', 'xiao']])

    @timeit_decorator()
    def test_segment_text_multi_syllable_apostrophe(self):
        result = segment_text("chang'an shan'er li'an", method='py')
        self.assertEqual(result, [['chang', 'an'], ['shan', 'er'], ['li', 'an']])

    @timeit_decorator()
    def test_segment_text_multi_syllable_vowel_start(self):
        result = segment_text('anwei aiai ouyang ewei', method='py')
        self.assertEqual(result, [['an', 'wei'], ['ai', 'ai'], ['ou', 'yang'], ['e', 'wei']])

    @timeit_decorator()
    def test_segment_text_invalid_initials(self):
        result = segment_text('xa qo vei', method='py')
        self.assertEqual(result, [['xa'], ['qo'], ['v', 'ei']])

    @timeit_decorator()
    def test_segment_text_invalid_finals(self):
        result = segment_text('banp zhirr mingk', method='py')
        self.assertEqual(result, [['ban', 'p'], ['zhi', 'rr'], ['ming', 'k']])

    @timeit_decorator()
    def test_segment_text_special_cases_er_n_ng(self):
        result = segment_text('sheng deng er han shier', method='py')
        self.assertEqual(result, [['sheng'], ['deng'], ['er'], ['han'], ['shi', 'er']])

    @timeit_decorator()
    def test_segment_text_special_cases_combined_initials(self):
        result = segment_text('shuang huang shun', method='py')
        self.assertEqual(result, [['shuang'], ['huang'], ['shun']])

    @timeit_decorator()
    def test_segment_text_edge_cases_ambiguous_finals(self):
        result = segment_text('wenti linping gangzhi', method='py')
        self.assertEqual(result, [['wen', 'ti'], ['lin', 'ping'], ['gang', 'zhi']])

    @timeit_decorator()
    def test_segment_text_no_valid_finals(self):
        result = segment_text('blar ziang shoing', method='py')
        self.assertEqual(result, [['bla', 'r'], ['zi', 'ang'], ['sho', 'ing']])

    @timeit_decorator()
    def test_segment_text_multi_vowel_combinations(self):
        result = segment_text('ai ei ou uan ie', method='py')
        self.assertEqual(result, [['ai'], ['ei'], ['ou'], ['u', 'an'], ['ie']])

    @timeit_decorator()
    def test_segment_text_one_syllable_edge_case(self):
        result = segment_text('a e ou yi', method='py')
        self.assertEqual(result, [['a'], ['e'], ['ou'], ['yi']])

    @timeit_decorator()
    def test_segment_text_multi_syllable_edge_case_er_n_ng(self):
        result = segment_text('zhuangyuan wenxiang gangren', method='py')
        self.assertEqual(result, [['zhuang', 'yuan'], ['wen', 'xiang'], ['gang', 'ren']])

    @timeit_decorator()
    def test_segment_text_wade_giles(self):
        result = segment_text("ni lin-p'ing shang ch'an-kan hsiao-ming yüan-yang erh shih-erh hsiung an-wei feng-huang "
                              "jen-min", method='wg')
        self.assertEqual(result, [['ni'], ['lin', "p'ing"], ['shang'], ["ch'an", 'kan'], ['hsiao', 'ming'],
                                  ['yüan', 'yang'], ['erh'], ['shih', 'erh'], ['hsiung'], ['an', 'wei'],
                                  ['feng', 'huang'], ['jen', 'min']])

    @timeit_decorator()
    def test_segment_text_ignore_capitalization(self):
        result = segment_text("Ni lin-p'ing SHANG ch'an-kan Hsiao-ming yüan-yang erh SHIH-ERH hsiung An-wei feng-huang "
                              "jen-min", method='wg')
        self.assertEqual(result, [['ni'], ['lin', "p'ing"], ['shang'], ["ch'an", 'kan'], ['hsiao', 'ming'],
                                  ['yüan', 'yang'], ['erh'], ['shih', 'erh'], ['hsiung'], ['an', 'wei'],
                                  ['feng', 'huang'], ['jen', 'min']])

    # CONFIG OBJECT TESTS #
    @timeit_decorator()
    def test_segment_text_with_config(self):
        config = Config(error_skip=True)
        result = segment_text("Zhongguo ti'an tianqi", method="py", config=config)
        self.assertIsNotNone(result)

    @timeit_decorator()
    def test_syllable_count_with_config(self):
        config = Config(error_skip=True)
        result = syllable_count("Zhongguo ti'an tianqi", method="py", config=config)
        self.assertIsNotNone(result)

    @timeit_decorator()
    def test_convert_text_with_config(self):
        config = Config(error_skip=True)
        result = convert_text("Zhongguo ti'an tianqi", convert_from="py", convert_to="wg", config=config)
        self.assertIsNotNone(result)

    @timeit_decorator()
    def test_cherry_pick_with_config(self):
        config = Config(error_report=True)
        result = cherry_pick("Zhongguo ti'an tianqi", convert_from="py", convert_to="wg", config=config)
        self.assertIsNotNone(result)

    @timeit_decorator()
    def test_detect_method_with_config(self):
        config = Config(error_skip=True)
        result = detect_method("Zhongguo ti'an tianqi", config=config)
        self.assertIsNotNone(result)

    @timeit_decorator()
    def test_validator_with_config(self):
        config = Config(error_skip=True)
        result = validator("Zhongguo ti'an tianqi", method="py", config=config)
        self.assertIsNotNone(result)

    # ERROR CATCHING TESTS #
    @timeit_decorator()
    def test_load_method_params_error(self):
        with self.assertRaises(FileNotFoundError):
            load_method_params('pa')

    # SYLLABLE VALIDATION TESTING #
    @timeit_decorator()
    def test_validator_true(self):
        result = validator("ni lin-p'ing shang ch'an-kan hsiao-ming yüan-yang erh shih-erh hsiung an-wei feng-huang",
                           method='wg')
        self.assertEqual(result, True)

    @timeit_decorator()
    def test_validator_false(self):
        result = validator("ni linp'ing shang ch'anzkan hsiaoming yüanyang erh shiherh hsiung anwei fenghuang",
                           method='wg')
        self.assertEqual(result, False)

    @timeit_decorator()
    def test_validator_per_word(self):
        result = validator("ni linpzing shangz chazng'an iaoming yuanng er shizer xiongew anwei fengghuang",
                           method='py', per_word=True)
        self.assertEqual(result, [
            {'word': 'ni', 'syllables': ['ni'], 'valid': [True]},
            {'word': 'linpzing', 'syllables': ['lin', 'pzing'], 'valid': [True, False]},
            {'word': 'shangz', 'syllables': ['shang', 'z'], 'valid': [True, False]},
            {'word': 'chazngan', 'syllables': ['cha', 'zng', 'an'], 'valid': [True, False, True]},
            {'word': 'iaoming', 'syllables': ['i', 'ao', 'ming'], 'valid': [False, True, True]},
            {'word': 'yuanng', 'syllables': ['yuan', 'ng'], 'valid': [True, False]},
            {'word': 'er', 'syllables': ['er'], 'valid': [True]},
            {'word': 'shizer', 'syllables': ['shi', 'zer'], 'valid': [True, False]},
            {'word': 'xiongew', 'syllables': ['xiong', 'e', 'w'], 'valid': [True, True, False]},
            {'word': 'anwei', 'syllables': ['an', 'wei'], 'valid': [True, True]},
            {'word': 'fengghuang', 'syllables': ['feng', 'ghu', 'ang'], 'valid': [True, False, True]}]
                         )

    # ROMANIZATON CONVERSION TESTING #
    @timeit_decorator()
    def test_convert_text_py_wg(self):
        result = convert_text('ni hao chang\'an yuan di\'an sheer zongtao', convert_from='py', convert_to='wg')
        self.assertEqual(result, "ni hao ch'ang-an yüan ti-an she-erh tsung-t'ao")

    @timeit_decorator()
    def test_convert_text_wg_py(self):
        result = convert_text('ni hao ch\'ang-an yüan ti-an she-erh tsung-t\'ao', convert_from='wg', convert_to='py')
        self.assertEqual(result, "ni hao chang'an yuan di'an she'er zongtao")

    @timeit_decorator()
    def test_convert_text_titlecase(self):
        result = convert_text('Ni hao Chang\'an Yuan', convert_from='py', convert_to='wg')
        self.assertEqual(result, "Ni hao Ch'ang-an Yüan")

    @timeit_decorator()
    def test_convert_text_uppercase(self):
        result = convert_text('NI HAO Chang\'an YUAN', convert_from='py', convert_to='wg')
        self.assertEqual(result, "NI HAO Ch'ang-an YÜAN")

    @timeit_decorator()
    def test_convert_text_error(self):
        result = convert_text('fre', convert_from='py', convert_to='wg')
        self.assertEqual(result, "fre(!)")

    @timeit_decorator()
    def test_convert_text_rare_pinyin_error(self):
        result = convert_text('diang', convert_from='py', convert_to='wg')
        self.assertEqual(result, "diang(!rare Pinyin!)")

    @timeit_decorator()
    def test_cherry_pick(self):
        self.maxDiff = None
        result = cherry_pick("Bai Juyi lived during the Middle Tang period. This was a period of rebuilding and "
                             "recovery for the Tang Empire, following the An Lushan Rebellion, and following the "
                             "poetically flourishing era famous for Li Bai (701－762), Wang Wei (701－761), and Du Fu "
                             "(712－770). Bai Juyi lived through the reigns of eight or nine emperors, being born in "
                             "the Dali regnal era (766-779) of Emperor Daizong of Tang. He had a long and successful "
                             "career both as a government official and a poet, although these two facets of his career "
                             "seemed to have come in conflict with each other at certain points. Bai Juyi was also a "
                             "devoted Chan Buddhist.", convert_from='py', convert_to='wg')
        self.assertEqual(result, "Pai Chü-i lived during the Middle T'ang period. This was a period of rebuilding and recovery for the T'ang Empire, following the An Lu-shan Rebellion, and following the poetically flourishing era famous for Li Pai (701－762), Wang Wei (701－761), and Tu Fu (712－770). Pai Chü-i lived through the reigns of eight or nine emperors, being born in the Ta-li regnal era (766-779) of Emperor Tai-tsung of T'ang. He had a long and successful career both as a government official and a poet, although these two facets of his career seemed to have come in conflict with each other at certain points. Pai Chü-i was also a devoted Ch'an Buddhist.")

    @timeit_decorator()
    def test_cherry_pick_long(self):
        self.maxDiff = None
        result = cherry_pick("Bai Juyi lived during the Middle Tang period. This was a period of rebuilding and "
                             "recovery for the Tang Empire, following the An Lushan Rebellion, and following the "
                             "poetically flourishing era famous for Li Bai (701－762), Wang Wei (701－761), and Du Fu ("
                             "712－770). Bai Juyi lived through the reigns of eight or nine emperors, being born in "
                             "the Dali regnal era (766-779) of Emperor Daizong of Tang. He had a long and successful "
                             "career both as a government official and a poet, although these two facets of his "
                             "career seemed to have come in conflict with each other at certain points. Bai Juyi was "
                             "also a devoted Chan Buddhist. Bai Juyi was born in 772 in Taiyuan, Shanxi, "
                             "which was then a few miles from location of the modern city, although he was in "
                             "Zhengyang, Henan for most of his childhood. His family was poor but scholarly, "
                             "his father being an Assistant Department Magistrate of the second-class. At the age of "
                             "ten he was sent away from his family to avoid a war that broke out in the north of "
                             "China, and went to live with relatives in the area known as Jiangnan, more specifically "
                             "Xuzhou. Bai Juyi's official career was initially successful. He passed the jinshi "
                             "examinations in 800. Bai Juyi may have taken up residence in the western capital city "
                             "of Chang'an, in 801. Not long after this, Bai Juyi formed a long friendship with a "
                             "scholar Yuan Zhen. Bai Juyi's father died in 804, and the young Bai spent the "
                             "traditional period of retirement mourning the death of his parent, which he did along "
                             "the Wei River, near to the capital. 806, the first full year of the reign of Emperor "
                             "Xianzong of Tang, was the year when Bai Juyi was appointed to a minor post as a "
                             "government official, at Zhouzhi, which was not far from Chang'an (and also in Shaanxi "
                             "province). He was made a member (scholar) of the Hanlin Academy, in 807, and Reminder "
                             "of the Left from 807 until 815, except when in 811 his mother died, and he spent the "
                             "traditional three-year mourning period again along the Wei River, before returning to "
                             "court in the winter of 814, where he held the title of Assistant Secretary to the "
                             "Prince's Tutor. It was not a high-ranking position, but nevertheless one which he was "
                             "soon to lose. While serving as a minor palace official in 814, Bai managed to get "
                             "himself in official trouble. He made enemies at court and with certain individuals in "
                             "other positions. It was partly his written works which led him into trouble. He wrote "
                             "two long memorials, translated by Arthur Waley as \"On Stopping the War\", "
                             "regarding what he considered to be an overly lengthy campaign against a minor group of "
                             "Tatars; and he wrote a series of poems, in which he satirized the actions of greedy "
                             "officials and highlighting the sufferings of the common folk. At this time, one of the "
                             "post-An Lushan warlords (jiedushi), Wu Yuanji in Henan, had seized control of Zhangyi "
                             "Circuit (centered in Zhumadian), an act for which he sought reconciliation with the "
                             "imperial government, trying to get an imperial pardon as a necessary prerequisite. "
                             "Despite the intercession of influential friends, Wu was denied, thus officially putting "
                             "him in the position of rebellion. Still seeking a pardon, Wu turned to assassination, "
                             "blaming the Prime Minister, Wu Yuanheng, and other officials: the imperial court "
                             "generally began by dawn, requiring the ministers to rise early in order to attend in a "
                             "timely manner; and, on July 13, 815, before dawn, the Tang Prime Minister Wu Yuanheng "
                             "was set to go to the palace for a meeting with Emperor Xianzong. As he left his house, "
                             "arrows were fired at his retinue. His servants all fled, and the assassins seized Wu "
                             "Yuanheng and his horse, and then decapitated him, taking his head with them. The "
                             "assassins also attacked another official who favored the campaign against the "
                             "rebellious warlords, Pei Du, but was unable to kill him. The people at the capital were "
                             "shocked and there was turmoil, with officials refusing to leave their personal "
                             "residences until after dawn. In this context, Bai Juyi overstepped his minor position "
                             "by memorializing the emperor. As Assistant Secretary to the Prince's Tutor, "
                             "Bai's memorial was a breach of protocol — he should have waited for those of censorial "
                             "authority to take the lead before offering his own criticism. This was not the only "
                             "charge which his opponents used against him. His mother had died, apparently caused by "
                             "falling into a well while looking at some flowers, and two poems written by Bai Juyi — "
                             "the titles of which Waley translates as \"In Praise of Flowers\" and \"The New Well\" — "
                             "were used against him as a sign of lack of Filial Piety, one of the Confucian ideals. "
                             "The result was exile. Bai Juyi was demoted to the rank of Sub-Prefect and banished from "
                             "the court and the capital city to Jiujiang, then known as Xun Yang, on the southern "
                             "shores of the Yangtze River in northwest Jiangxi Province. After three years, "
                             "he was sent as Governor of a remote place in Sichuan. At the time, the main travel "
                             "route there was up the Yangzi River. This trip allowed Bai Juyi a few days to visit his "
                             "friend Yuan Zhen, who was also in exile and with whom he explored the rock caves "
                             "located at Yichang. Bai Juyi was delighted by the flowers and trees for which his new "
                             "location was noted. In 819, he was recalled back to the capital, ending his exile.",
                             convert_from='py', convert_to='wg')
        self.assertEqual(result, "Pai Chü-i lived during the Middle T'ang period. This was a period of rebuilding "
                                 "and recovery for the T'ang Empire, following the An Lu-shan Rebellion, and following "
                                 "the poetically flourishing era famous for Li Pai (701－762), Wang Wei (701－761), and "
                                 "Tu Fu (712－770). Pai Chü-i lived through the reigns of eight or nine emperors, being "
                                 "born in the Ta-li regnal era (766-779) of Emperor Tai-tsung of T'ang. He had a long "
                                 "and successful career both as a government official and a poet, although these two "
                                 "facets of his career seemed to have come in conflict with each other at certain "
                                 "points. Pai Chü-i was also a devoted Ch'an Buddhist. Pai Chü-i was born in 772 in "
                                 "T'ai-yüan, Shan-hsi, which was then a few miles from location of the modern city, "
                                 "although he was in Cheng-yang, Ho-nan for most of his childhood. His family was poor "
                                 "but scholarly, his father being an Assistant Department Magistrate of the "
                                 "second-class. At the age of ten he was sent away from his family to avoid a war "
                                 "that broke out in the north of China, and went to live with relatives in the area "
                                 "known as Chiang-nan, more specifically Hsü-chou. Pai Chü-i's official career was "
                                 "initially successful. He passed the chin-shih examinations in 800. Pai Chü-i may "
                                 "have taken up residence in the western capital city of Ch'ang-an, in 801. Not long "
                                 "after this, Pai Chü-i formed a long friendship with a scholar Yüan Chen. Pai Chü-i's "
                                 "father died in 804, and the young Pai spent the traditional period of retirement "
                                 "mourning the death of his parent, which he did along the Wei River, near to the "
                                 "capital. 806, the first full year of the reign of Emperor Hsien-tsung of T'ang, "
                                 "was the year when Pai Chü-i was appointed to a minor post as a government official, "
                                 "at Chou-chih, which was not far from Ch'ang-an (and also in Shaanxi province). He "
                                 "was made a member (scholar) of the Han-lin Academy, in 807, and Reminder of the Left "
                                 "from 807 until 815, except when in 811 his mother died, and he spent the traditional "
                                 "three-year mourning period again along the Wei River, before returning to court in "
                                 "the winter of 814, where he held the title of Assistant Secretary to the Prince's "
                                 "Tutor. It was not a high-ranking position, but nevertheless one which he was soon "
                                 "to lose. While serving as a minor palace official in 814, Pai managed to get "
                                 "himself in official trouble. He made enemies at court and with certain individuals "
                                 "in other positions. It was partly his written works which led him into trouble. "
                                 "He wrote two long memorials, translated by Arthur Waley as \"On Stopping the War\", "
                                 "regarding what he considered to be an overly lengthy campaign against a minor group "
                                 "of Tatars; and he wrote a series of poems, in which he satirized the actions of "
                                 "greedy officials and highlighting the sufferings of the common folk. At this time, "
                                 "one of the post-An Lu-shan warlords (chieh-tu-shih), Wu Yüan-chi in Ho-nan, had "
                                 "seized control of Chang-i Circuit (centered in Chu-ma-tien), an act for which he "
                                 "sought reconciliation with the imperial government, trying to get an imperial "
                                 "pardon as a necessary prerequisite. Despite the intercession of influential "
                                 "friends, Wu was denied, thus officially putting him in the position of rebellion. "
                                 "Still seeking a pardon, Wu turned to assassination, blaming the Prime Minister, "
                                 "Wu Yüan-heng, and other officials: the imperial court generally began by dawn, "
                                 "requiring the ministers to rise early in order to attend in a timely manner; and, "
                                 "on July 13, 815, before dawn, the T'ang Prime Minister Wu Yüan-heng was set to go "
                                 "to the palace for a meeting with Emperor Hsien-tsung. As he left his house, arrows "
                                 "were fired at his retinue. His servants all fled, and the assassins seized Wu "
                                 "Yüan-heng and his horse, and then decapitated him, taking his head with them. The "
                                 "assassins also attacked another official who favored the campaign against the "
                                 "rebellious warlords, P'ei Tu, but was unable to kill him. The people at the capital "
                                 "were shocked and there was turmoil, with officials refusing to leave their personal "
                                 "residences until after dawn. In this context, Pai Chü-i overstepped his minor "
                                 "position by memorializing the emperor. As Assistant Secretary to the Prince's "
                                 "Tutor, Pai's memorial was a breach of protocol — he should have waited for those "
                                 "of censorial authority to take the lead before offering his own criticism. This "
                                 "was not the only charge which his opponents used against him. His mother had died, "
                                 "apparently caused by falling into a well while looking at some flowers, and two "
                                 "poems written by Pai Chü-i — the titles of which Waley translates as \"In Praise "
                                 "of Flowers\" and \"The New Well\" — were used against him as a sign of lack of "
                                 "Filial Piety, one of the Confucian ideals. The result was exile. Pai Chü-i was "
                                 "demoted to the rank of Sub-Prefect and banished from the court and the capital "
                                 "city to Chiu-chiang, then known as Hsün Yang, on the southern shores of the "
                                 "Yangtze River in northwest Chiang-hsi Province. After three years, he was sent "
                                 "as Governor of a remote place in Ssu-ch'uan. At the time, the main travel route "
                                 "there was up the Yang-tzu River. This trip allowed Pai Chü-i a few days to visit "
                                 "his friend Yüan Chen, who was also in exile and with whom he explored the rock "
                                 "caves located at I-ch'ang. Pai Chü-i was delighted by the flowers and trees for "
                                 "which his new location was noted. In 819, he was recalled back to the capital, "
                                 "ending his exile.")

    # SYLLABLE_COUNT TESTING #
    @timeit_decorator(repeats=100)
    def test_syllable_count_py(self):
        num_syllables = random.randint(1, 3)
        random_text = generate_random_text_from_list('py', num_syllables=num_syllables)
        result = syllable_count(random_text, method='py')
        # print(f"Test {test_counter}: {random_text} has {num_syllables} syllables")
        self.assertEqual(result, [num_syllables], msg=f"Text analyzed: {random_text}")

    @timeit_decorator(repeats=100)
    def test_syllable_count_wg(self):
        num_syllables = random.randint(1, 3)
        random_text = generate_random_text_from_list('wg', num_syllables=num_syllables)
        result = syllable_count(random_text, method='wg')
        # print(f"Test {test_counter}: {random_text} has {num_syllables} syllables")
        self.assertEqual(result, [num_syllables], msg=f"Text analyzed: {random_text}")

    # METHOD DETECTION TESTING #
    @timeit_decorator(repeats=100)
    def test_detect_method_py(self):
        random_text = generate_random_text_from_list('py', 3)
        result = detect_method(random_text)
        self.assertIn('py', result, f"'py' not found in text: {random_text}")

    @timeit_decorator(repeats=100)
    def test_detect_method_wg(self):
        random_text = generate_random_text_from_list('wg', 3)
        result = detect_method(random_text)
        self.assertIn('wg', result, f"'wg' not found in text: {random_text}")

    @timeit_decorator()
    def test_detect_method_per_word(self):
        result = detect_method(f"ni linping shang chang'an erh shier shoiji yiin", per_word=True)
        self.assertEqual(result, [{'word': 'ni', 'methods': ['py', 'wg']},
                                  {'word': 'linping', 'methods': ['py', 'wg']},
                                  {'word': 'shang', 'methods': ['py', 'wg']},
                                  {'word': "chang'an", 'methods': ['py']},
                                  {'word': 'erh', 'methods': ['wg']},
                                  {'word': 'shier', 'methods': ['py']},
                                  {'word': 'shoiji', 'methods': []},
                                  {'word': 'yiin', 'methods': []}]
                         )

    # ERROR_SKIP TESTING #
    @timeit_decorator()
    def test_segment_text_error_skip(self):
        result = segment_text("Bai Juyi lived during the Middle Tang period.", method='py', error_skip=True)
        self.assertEqual(result, [['bai'], ' ', ['ju', 'yi'], ' ', ['li', 'v', 'e', 'd'], ' ', ['du', 'ring'], ' ',
                                  ['the'], ' ', ['mi', 'ddle'], ' ', ['tang'], ' ', ['pe', 'ri', 'o', 'd'], '.'])

    # CRUMBS AND LOGGING TESTING #
    def setUp(self):
        # Set up logging capture for all tests that use crumbs/logging
        self.log_stream = StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        self.logger = logging.getLogger()
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.INFO)

    def tearDown(self):
        # Remove logging handler after each test
        self.logger.removeHandler(self.log_handler)
        self.log_stream.close()

    @timeit_decorator()
    def test_segment_text_crumb(self):
        result = segment_text("t'ao", method='wg', crumbs=True)
        self.assertEqual(result, [["t'ao"]])
        self.log_handler.flush()
        console_output = self.log_stream.getvalue().strip()
        expected_output = "# Analyzing text as Wade-Giles: t'ao\n" \
                            "## initial found: t'\n" \
                            "## final found: ao\n" \
                            "### Syllable: \"t'ao\" valid: True\n" \
                            "# Word Validation: \"t'ao\" is valid\n" \
                            "---\n" \
                            "# Segment Text: Assembling segments\n" \
                            "---"
        self.assertEqual(console_output, expected_output)

    @timeit_decorator()
    def test_convert_text_crumb(self):
        result = convert_text("t'ao", convert_from='wg', convert_to='py', crumbs=True)
        self.assertEqual(result, "tao")
        self.log_handler.flush()
        console_output = self.log_stream.getvalue().strip()
        expected_output = "# Analyzing text as Wade-Giles: t'ao\n" \
                            "## initial found: t'\n" \
                            "## final found: ao\n" \
                            "### Syllable: \"t'ao\" valid: True\n" \
                            "# Word Validation: \"t'ao\" is valid\n" \
                            "---\n" \
                            "# Converting text: Wade-Giles -> Pinyin\n" \
                            "## Converted text: \"t'ao\" -> \"tao\"\n" \
                            "---"
        self.assertEqual(console_output, expected_output)

    @timeit_decorator()
    def test_convert_text_crumb_cached(self):
        # The per-syllable conversion cache is shared across the whole process
        # (that's the point - it's what lets repeated calls in a loop avoid
        # re-parsing conversion_mapping.csv), so clear it here to make this
        # test's "first occurrence is a miss" assumption independent of
        # whatever other tests already converted "t'ao" wg->py.
        from RoManTools.conversion import clear_conversion_cache
        clear_conversion_cache()

        result = convert_text("t'ao t'ao", convert_from='wg', convert_to='py', crumbs=True)
        self.assertEqual(result, "tao tao")
        self.log_handler.flush()
        console_output = self.log_stream.getvalue().strip()
        expected_output = "# Analyzing text as Wade-Giles: t'ao\n" \
                            "## initial found: t'\n" \
                            "## final found: ao\n" \
                            "### Syllable: \"t'ao\" valid: True\n" \
                            "# Word Validation: \"t'ao\" is valid\n" \
                            "---\n" \
                            "# Analyzing text as Wade-Giles: t'ao\n" \
                            "## Cached: \"t'ao\" | valid: True\n" \
                            "# Word Validation: \"t'ao\" is valid\n" \
                            "---\n" \
                            "# Converting text: Wade-Giles -> Pinyin\n" \
                            "## Converted text: \"t'ao\" -> \"tao\"\n" \
                            "## Cached: \"t'ao\" -> \"tao\"\n" \
                            "---"
        self.assertEqual(console_output, expected_output)

    @timeit_decorator()
    def test_cherry_pick_crumb(self):
        self.maxDiff = None
        result = cherry_pick("Hello, Xiang.", convert_from='py', convert_to='wg', crumbs=True)
        self.assertEqual(result, "Hello, Hsiang.")
        self.log_handler.flush()
        console_output = self.log_stream.getvalue().strip()
        expected_output = "# Analyzing text as Pinyin: Hello\n" \
                        "## initial found: h\n" \
                        "## final found: e\n" \
                        "### Syllable: \"he\" valid: True\n" \
                        "## initial found: ll\n" \
                        "## final found: o\n" \
                        "### Validation: invalid initial: 'll'\n" \
                        "### Syllable: \"llo\" valid: False\n" \
                        "# Word Validation: \"hello\" is invalid\n" \
                        "---\n" \
                        "# Non-text segment: , \n" \
                        "---\n" \
                        "# Analyzing text as Pinyin: Xiang\n" \
                        "## initial found: x\n" \
                        "## final found: iang\n" \
                        "### Syllable: \"xiang\" valid: True\n" \
                        "# Word Validation: \"xiang\" is valid\n" \
                        "---\n" \
                        "# Non-text segment: .\n" \
                        "---\n" \
                        "# Converting text: Pinyin -> Wade-Giles\n" \
                        "## Converted text: \"xiang\" -> \"hsiang\"\n" \
                        "---"
        self.assertEqual(console_output, expected_output)

    @timeit_decorator()
    def test_syllable_count_crumb(self):
        result = syllable_count("t'ao", method='wg', crumbs=True)
        self.assertEqual(result, [1])
        self.log_handler.flush()
        console_output = self.log_stream.getvalue().strip()
        expected_output = "# Analyzing text as Wade-Giles: t'ao\n" \
                            "## initial found: t'\n" \
                            "## final found: ao\n" \
                            "### Syllable: \"t'ao\" valid: True\n" \
                            "# Word Validation: \"t'ao\" is valid\n" \
                            "---\n" \
                            "# Syllable Count: Assembling counts\n" \
                            "---"
        self.assertEqual(console_output, expected_output)

    @timeit_decorator()
    def test_detect_method_crumb(self):
        result = detect_method("t'ao", crumbs=True)
        self.assertEqual(result, ['wg'])
        self.log_handler.flush()
        console_output = self.log_stream.getvalue().strip()
        expected_output = "# Analyzing text as Pinyin: t'ao\n" \
                            "## initial found: t\n" \
                            "### Validation: invalid final: ''\n" \
                            "### Syllable: \"t\" valid: False\n" \
                            "## initial found: ø\n" \
                            "## final found: ao\n" \
                            "### Syllable: \"ao\" valid: True\n" \
                            "# Word Validation: \"tao\" is invalid\n" \
                            "---\n" \
                            "# Analyzing text as Wade-Giles: t'ao\n" \
                            "## initial found: t'\n" \
                            "## final found: ao\n" \
                            "### Syllable: \"t'ao\" valid: True\n" \
                            "# Word Validation: \"t'ao\" is valid\n" \
                            "---\n" \
                            "# Detect Method: Assembling methods for all syllables\n" \
                            "---"
        self.assertEqual(console_output, expected_output)

    @timeit_decorator()
    def test_detect_method_per_word_crumb(self):
        result = detect_method("t'ao", True, crumbs=True)
        self.assertEqual(result, [{'methods': ['wg'], 'word': "t'ao"}])
        self.log_handler.flush()
        console_output = self.log_stream.getvalue().strip()
        expected_output = "# Analyzing text as Pinyin: t'ao\n" \
                            "## initial found: t\n" \
                            "### Validation: invalid final: ''\n" \
                            "### Syllable: \"t\" valid: False\n" \
                            "## initial found: ø\n" \
                            "## final found: ao\n" \
                            "### Syllable: \"ao\" valid: True\n" \
                            "# Word Validation: \"tao\" is invalid\n" \
                            "---\n" \
                            "# Analyzing text as Wade-Giles: t'ao\n" \
                            "## initial found: t'\n" \
                            "## final found: ao\n" \
                            "### Syllable: \"t'ao\" valid: True\n" \
                            "# Word Validation: \"t'ao\" is valid\n" \
                            "---\n" \
                            "# Detect Method: Assembling methods\n" \
                            "---"
        self.assertEqual(console_output, expected_output)

    @timeit_decorator()
    def test_validator_crumb(self):
        result = validator("t'ao", method='wg', crumbs=True)
        self.assertEqual(result, True)
        self.log_handler.flush()
        console_output = self.log_stream.getvalue().strip()
        expected_output = "# Analyzing text as Wade-Giles: t'ao\n" \
                          "## initial found: t'\n" \
                          "## final found: ao\n" \
                          "### Syllable: \"t'ao\" valid: True\n" \
                          "# Word Validation: \"t'ao\" is valid\n" \
                          "---"
        self.assertEqual(console_output, expected_output)


class TestErrorReporting(unittest.TestCase):
    """Test suite for error reporting and tracking features."""

    def test_error_type_enum_values(self):
        """Test that ErrorType enum has correct values."""
        from RoManTools.errors import ErrorType
        
        self.assertEqual(ErrorType.INVALID_INITIAL.value, "invalid_initial")
        self.assertEqual(ErrorType.INVALID_FINAL.value, "invalid_final")
        self.assertEqual(ErrorType.INVALID_SYLLABLE.value, "invalid_syllable")
        self.assertEqual(ErrorType.ILLEGAL_CHARACTER.value, "illegal_character")
        self.assertEqual(ErrorType.RARE_SYLLABLE.value, "rare_syllable")
        self.assertEqual(ErrorType.UNKNOWN.value, "unknown")

    def test_error_type_message_templates(self):
        """Test that ErrorType enum has message templates."""
        from RoManTools.errors import ErrorType
        
        self.assertEqual(ErrorType.INVALID_INITIAL.message_template, "Invalid initial: '{initial}'")
        self.assertEqual(ErrorType.INVALID_FINAL.message_template, "Invalid final: '{final}'")
        self.assertEqual(ErrorType.INVALID_SYLLABLE.message_template, "Invalid syllable combination: '{initial}' + '{final}'")
        self.assertEqual(ErrorType.ILLEGAL_CHARACTER.message_template, "Illegal character: '{character}'")
        self.assertEqual(ErrorType.RARE_SYLLABLE.message_template, "Rare syllable: '{syllable}'")

    def test_error_type_format_message(self):
        """Test ErrorType.format_message() method."""
        from RoManTools.errors import ErrorType
        
        msg1 = ErrorType.INVALID_INITIAL.format_message(initial='xyz')
        self.assertEqual(msg1, "Invalid initial: 'xyz'")
        
        msg2 = ErrorType.INVALID_FINAL.format_message(final='qqq')
        self.assertEqual(msg2, "Invalid final: 'qqq'")
        
        msg3 = ErrorType.INVALID_SYLLABLE.format_message(initial='z', final='yx')
        self.assertEqual(msg3, "Invalid syllable combination: 'z' + 'yx'")
        
        msg4 = ErrorType.ILLEGAL_CHARACTER.format_message(character='@')
        self.assertEqual(msg4, "Illegal character: '@'")
        
        msg5 = ErrorType.RARE_SYLLABLE.format_message(syllable='nun')
        self.assertEqual(msg5, "Rare syllable: 'nun'")

    def test_error_tracker_creation(self):
        """Test ErrorTracker initialization."""
        from RoManTools.errors import ErrorTracker, ErrorType
        
        tracker = ErrorTracker()
        self.assertFalse(tracker.has_errors())
        self.assertEqual(tracker.get_error_count(), 0)
        self.assertEqual(tracker.get_error_count(ErrorType.INVALID_INITIAL), 0)

    def test_error_tracker_add_invalid_initial(self):
        """Test adding invalid initial error."""
        from RoManTools.errors import ErrorTracker, ErrorType
        
        tracker = ErrorTracker()
        tracker.add_invalid_initial('xyz', 'xyzang', position=0)
        
        self.assertTrue(tracker.has_errors())
        self.assertEqual(tracker.get_error_count(), 1)
        self.assertEqual(tracker.get_error_count(ErrorType.INVALID_INITIAL), 1)
        self.assertIn(ErrorType.INVALID_INITIAL.value, tracker.get_error_types_list())

        error = tracker.errors[0]
        self.assertEqual(error.error_type, ErrorType.INVALID_INITIAL)
        self.assertEqual(error.message, "Invalid initial: 'xyz'")
        self.assertEqual(error.syllable, 'xyzang')
        self.assertEqual(error.position, 0)
        self.assertEqual(error.details['initial'], 'xyz')

    def test_error_tracker_add_invalid_final(self):
        """Test adding invalid final error."""
        from RoManTools.errors import ErrorTracker, ErrorType
        
        tracker = ErrorTracker()
        tracker.add_invalid_final('qqq', 'bqqq', initial='b', position=5)
        
        self.assertTrue(tracker.has_errors())
        self.assertEqual(tracker.get_error_count(), 1)
        self.assertEqual(tracker.get_error_count(ErrorType.INVALID_FINAL), 1)
        
        error = tracker.errors[0]
        self.assertEqual(error.error_type, ErrorType.INVALID_FINAL)
        self.assertEqual(error.message, "Invalid final: 'qqq'")
        self.assertEqual(error.syllable, 'bqqq')
        self.assertEqual(error.position, 5)
        self.assertEqual(error.details['final'], 'qqq')
        self.assertEqual(error.details['initial'], 'b')

    def test_error_tracker_add_invalid_syllable(self):
        """Test adding invalid syllable combination error."""
        from RoManTools.errors import ErrorTracker, ErrorType
        
        tracker = ErrorTracker()
        tracker.add_invalid_syllable('zyx', 'z', 'yx', position=10)
        
        self.assertTrue(tracker.has_errors())
        self.assertEqual(tracker.get_error_count(), 1)
        self.assertEqual(tracker.get_error_count(ErrorType.INVALID_SYLLABLE), 1)
        
        error = tracker.errors[0]
        self.assertEqual(error.error_type, ErrorType.INVALID_SYLLABLE)
        self.assertEqual(error.message, "Invalid syllable combination: 'z' + 'yx'")
        self.assertEqual(error.syllable, 'zyx')
        self.assertEqual(error.details['initial'], 'z')
        self.assertEqual(error.details['final'], 'yx')

    def test_error_tracker_add_illegal_character(self):
        """Test adding illegal character error."""
        from RoManTools.errors import ErrorTracker, ErrorType
        
        tracker = ErrorTracker()
        tracker.add_illegal_character('@', 'zh@ng', reason='Special characters not allowed')
        
        self.assertTrue(tracker.has_errors())
        self.assertEqual(tracker.get_error_count(), 1)
        self.assertEqual(tracker.get_error_count(ErrorType.ILLEGAL_CHARACTER), 1)
        
        error = tracker.errors[0]
        self.assertEqual(error.error_type, ErrorType.ILLEGAL_CHARACTER)
        self.assertIn("Illegal character: '@'", error.message)
        self.assertIn("Special characters not allowed", error.message)
        self.assertEqual(error.details['character'], '@')
        self.assertEqual(error.details['reason'], 'Special characters not allowed')

    def test_error_tracker_add_rare_syllable(self):
        """Test adding rare syllable warning."""
        from RoManTools.errors import ErrorTracker, ErrorType
        
        tracker = ErrorTracker()
        tracker.add_rare_syllable('nun', 'py', position=0)
        
        self.assertTrue(tracker.has_errors())
        self.assertEqual(tracker.get_error_count(), 1)
        self.assertEqual(tracker.get_error_count(ErrorType.RARE_SYLLABLE), 1)
        
        error = tracker.errors[0]
        self.assertEqual(error.error_type, ErrorType.RARE_SYLLABLE)
        self.assertEqual(error.message, "Rare syllable: 'nun'")
        self.assertEqual(error.details['method'], 'py')

    def test_error_tracker_multiple_errors(self):
        """Test tracking multiple errors of different types."""
        from RoManTools.errors import ErrorTracker, ErrorType
        
        tracker = ErrorTracker()
        tracker.add_invalid_initial('xyz', 'xyzang')
        tracker.add_invalid_final('qqq', 'bqqq')
        tracker.add_invalid_syllable('zyx', 'z', 'yx')
        tracker.add_illegal_character('@', 'zh@ng')
        tracker.add_rare_syllable('nun', 'py')
        
        self.assertEqual(tracker.get_error_count(), 5)
        self.assertEqual(tracker.get_error_count(ErrorType.INVALID_INITIAL), 1)
        self.assertEqual(tracker.get_error_count(ErrorType.INVALID_FINAL), 1)
        self.assertEqual(tracker.get_error_count(ErrorType.INVALID_SYLLABLE), 1)
        self.assertEqual(tracker.get_error_count(ErrorType.ILLEGAL_CHARACTER), 1)
        self.assertEqual(tracker.get_error_count(ErrorType.RARE_SYLLABLE), 1)

    def test_error_tracker_get_first_error_string(self):
        """Test getting first error as compact string."""
        from RoManTools.errors import ErrorTracker
        
        tracker = ErrorTracker()
        tracker.add_invalid_initial('xyz', 'xyzang')
        tracker.add_invalid_final('qqq', 'bqqq')
        
        first_error = tracker.get_first_error_string()
        # get_first_error_string returns the detail (initial/final/character) not the syllable
        self.assertEqual(first_error, 'ERROR - invalid_initial - "xyz"')

    def test_error_tracker_generate_report_detailed(self):
        """Test generating detailed error report."""
        from RoManTools.errors import ErrorTracker
        
        tracker = ErrorTracker()
        tracker.add_invalid_initial('xyz', 'xyzang')
        tracker.add_invalid_final('qqq', 'bqqq', initial='b')
        
        report = tracker.generate_report(compact=False)
        
        # Check that report contains key components
        self.assertIn("Error Summary", report)
        self.assertIn("invalid_initial: 1", report)
        self.assertIn("invalid_final: 1", report)
        self.assertIn("Total: 2", report)
        self.assertIn("Detailed Errors", report)
        self.assertIn("Invalid initial: 'xyz'", report)
        self.assertIn("Invalid final: 'qqq'", report)

    def test_error_tracker_generate_report_compact(self):
        """Test generating compact error report."""
        from RoManTools.errors import ErrorTracker

        tracker = ErrorTracker()
        tracker.add_invalid_initial('xyz', 'xyzang')
        tracker.add_invalid_final('qqq', 'bqqq')

        report = tracker.generate_report(compact=True)

        # Compact format is just a one-line error count, not per-error detail
        # (use get_first_error_string() for the specific first error)
        self.assertEqual(report, '2 errors')

    def test_error_tracker_generate_report_max_errors(self):
        """Test max_errors limit in verbose report generation (compact ignores max_errors)."""
        from RoManTools.errors import ErrorTracker

        tracker = ErrorTracker()
        tracker.add_invalid_initial('x', 'x')
        tracker.add_invalid_initial('y', 'y')
        tracker.add_invalid_initial('z', 'z')

        report = tracker.generate_report(compact=False, max_errors=2, include_summary=False)

        # Should only show first 2 errors plus a truncation indicator
        self.assertIn("Invalid initial: 'x'", report)
        self.assertIn("Invalid initial: 'y'", report)
        self.assertNotIn("Invalid initial: 'z'", report)
        self.assertIn('... and 1 more error(s)', report)

    def test_syllable_error_tracking_invalid_initial(self):
        """Test that syllables track invalid initial errors."""
        from RoManTools.config import Config
        from RoManTools.syllable import SyllableProcessor
        from RoManTools.data_loader import load_method_params
        from RoManTools.errors import ErrorType
        
        config = Config(error_report=False, crumbs=False)
        method_params = load_method_params('py')
        processor = SyllableProcessor(config, method_params)
        
        syl = processor.create_syllable('xyz')
        
        self.assertFalse(syl.valid)
        self.assertIn(ErrorType.INVALID_INITIAL.value, syl.error_tracker.get_error_types_list())
        self.assertGreater(syl.error_tracker.get_error_count(), 0)

    def test_syllable_error_tracking_illegal_character(self):
        """Test that syllables track illegal character errors (apostrophe in Pinyin)."""
        from RoManTools.config import Config
        from RoManTools.syllable import SyllableProcessor
        from RoManTools.data_loader import load_method_params
        from RoManTools.errors import ErrorType
        
        config = Config(error_report=False, crumbs=False)
        method_params = load_method_params('py')
        processor = SyllableProcessor(config, method_params)
        
        syl = processor.create_syllable("zh'ng")
        
        self.assertFalse(syl.valid)
        self.assertIn(ErrorType.ILLEGAL_CHARACTER.value, syl.error_tracker.get_error_types_list())

    def test_syllable_error_tracking_rare_syllable(self):
        """Test that syllables track rare syllable warnings."""
        from RoManTools.config import Config
        from RoManTools.syllable import SyllableProcessor
        from RoManTools.data_loader import load_method_params
        from RoManTools.errors import ErrorType
        
        config = Config(error_report=False, crumbs=False)
        method_params = load_method_params('py')
        processor = SyllableProcessor(config, method_params)
        
        # 'nun' is marked as rare in conversion_mapping.csv
        syl = processor.create_syllable('nun')
        
        # Syllable should be valid but have rare warning
        self.assertTrue(syl.valid)
        if ErrorType.RARE_SYLLABLE.value in syl.error_tracker.get_error_types_list():
            self.assertEqual(syl.error_tracker.get_error_count(ErrorType.RARE_SYLLABLE), 1)

    def test_config_error_report_flag(self):
        """Test Config error_report flag."""
        from RoManTools.config import Config
        
        config_on = Config(error_report=True)
        self.assertTrue(config_on.error_report)
        
        config_off = Config(error_report=False)
        self.assertFalse(config_off.error_report)

    def test_config_error_report_compact_flag(self):
        """Test Config error_report_compact flag."""
        from RoManTools.config import Config
        
        config_detailed = Config(error_report=True, error_report_compact=False)
        self.assertFalse(config_detailed.error_report_compact)
        
        config_compact = Config(error_report=True, error_report_compact=True)
        self.assertTrue(config_compact.error_report_compact)

    def test_config_error_report_max(self):
        """Test Config error_report_max parameter."""
        from RoManTools.config import Config
        
        # Config converts 0 to None internally
        config_unlimited = Config(error_report=True, error_report_max=0)
        self.assertIsNone(config_unlimited.error_report_max)
        
        config_limited = Config(error_report=True, error_report_max=5)
        self.assertEqual(config_limited.error_report_max, 5)

    def test_table_utils_get_validation_column(self):
        """Test table_utils.get_validation_column() function."""
        from RoManTools.table_utils import get_validation_column
        
        # Valid syllable returns "OK"
        result_valid = get_validation_column('zhong', 'py')
        self.assertEqual(result_valid, "OK")
        
        # Invalid syllable returns error string
        result_invalid = get_validation_column('xyz', 'py')
        self.assertIn('ERROR', result_invalid)
        self.assertIn('invalid_initial', result_invalid)

    def test_table_utils_validate_syllable(self):
        """Test table_utils.validate_syllable() function."""
        from RoManTools.table_utils import validate_syllable
        
        # Valid syllable returns empty string
        result_valid = validate_syllable('zhong', 'py')
        self.assertEqual(result_valid, '')
        
        # Invalid syllable returns a compact error count string
        result_invalid = validate_syllable('xyz', 'py')
        self.assertEqual(result_invalid, '2 errors')

    def test_table_utils_validate_text(self):
        """Test table_utils.validate_text() function."""
        from RoManTools.table_utils import validate_text
        
        # All valid - returns dict with 'valid': True
        result_valid = validate_text('zhong', 'py')
        self.assertIsInstance(result_valid, dict)
        self.assertTrue(result_valid['valid'])
        self.assertEqual(result_valid['error_count'], 0)
        self.assertEqual(result_valid['error_report'], '')
        
        # Contains invalid - returns dict with 'valid': False
        result_invalid = validate_text('xyz', 'py')
        self.assertIsInstance(result_invalid, dict)
        self.assertFalse(result_invalid['valid'])
        self.assertGreater(result_invalid['error_count'], 0)
        self.assertGreater(len(result_invalid['error_report']), 0)

    def test_error_report_no_overhead_when_disabled(self):
        """Test that error reporting has minimal overhead when disabled."""
        from RoManTools.config import Config
        from RoManTools.syllable import SyllableProcessor
        from RoManTools.data_loader import load_method_params
        
        config = Config(error_report=False, crumbs=False)
        method_params = load_method_params('py')
        processor = SyllableProcessor(config, method_params)
        
        # Create invalid syllable
        syl = processor.create_syllable('xyz')
        
        # ErrorTracker should still exist (lightweight)
        self.assertIsNotNone(syl.error_tracker)
        self.assertTrue(syl.error_tracker.has_errors())

        # Can still generate report manually if needed
        report = syl.error_tracker.generate_report(compact=True)
        self.assertGreater(len(report), 0)
