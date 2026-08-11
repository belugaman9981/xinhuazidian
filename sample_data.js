// Sample data — a small, hand-picked slice of characters used as a
// fallback when jianzi_data.json (built by build_unihan_data.py) isn't
// available yet. The radical table itself now lives in radicals_full.js
// (all 214 Kangxi radicals) — this file only supplies sample characters.
//
// entries: word, radicalNo, residualStrokes (strokes beyond the radical), pinyin, def
const SAMPLE_ENTRIES = [
  { w:"亿", r:9,  rs:2, py:"yì",    def:"hundred million" },
  { w:"他", r:9,  rs:3, py:"tā",    def:"he; him" },
  { w:"们", r:9,  rs:3, py:"men",  def:"plural marker for pronouns" },
  { w:"你", r:9,  rs:5, py:"nǐ",    def:"you" },
  { w:"做", r:9,  rs:9, py:"zuò",  def:"to do; to make" },

  { w:"只", r:30, rs:2, py:"zhǐ",  def:"only" },
  { w:"叫", r:30, rs:2, py:"jiào", def:"to call; to shout" },
  { w:"号", r:30, rs:2, py:"hào",  def:"number; name" },
  { w:"吗", r:30, rs:3, py:"ma",   def:"question particle" },
  { w:"听", r:30, rs:4, py:"tīng", def:"to listen" },

  { w:"在", r:32, rs:3, py:"zài",  def:"at; in; located" },
  { w:"地", r:32, rs:3, py:"dì",   def:"earth; ground; place" },
  { w:"场", r:32, rs:3, py:"chǎng",def:"field; site" },
  { w:"城", r:32, rs:6, py:"chéng",def:"city; city wall" },

  { w:"好", r:38, rs:3, py:"hǎo",  def:"good" },
  { w:"妈", r:38, rs:3, py:"mā",   def:"mom" },
  { w:"姐", r:38, rs:5, py:"jiě",  def:"older sister" },
  { w:"妹", r:38, rs:5, py:"mèi",  def:"younger sister" },
  { w:"姓", r:38, rs:5, py:"xìng", def:"surname" },

  { w:"字", r:39, rs:3, py:"zì",   def:"character; word" },
  { w:"学", r:39, rs:5, py:"xué",  def:"to study; to learn" },
  { w:"孩", r:39, rs:6, py:"hái",  def:"child" },

  { w:"岁", r:46, rs:3, py:"suì",  def:"year of age" },
  { w:"岛", r:46, rs:4, py:"dǎo",  def:"island" },
  { w:"峰", r:46, rs:7, py:"fēng", def:"peak; summit" },

  { w:"忙", r:61, rs:3, py:"máng", def:"busy" },
  { w:"快", r:61, rs:4, py:"kuài", def:"fast; quick" },
  { w:"想", r:61, rs:9, py:"xiǎng",def:"to think; to want" },
  { w:"意", r:61, rs:9, py:"yì",   def:"meaning; idea" },

  { w:"打", r:64, rs:2, py:"dǎ",   def:"to hit; to play" },
  { w:"找", r:64, rs:4, py:"zhǎo", def:"to look for" },
  { w:"拿", r:64, rs:6, py:"ná",   def:"to hold; to take" },
  { w:"提", r:64, rs:9, py:"tí",   def:"to raise; to carry" },

  { w:"早", r:72, rs:2, py:"zǎo",  def:"early" },
  { w:"时", r:72, rs:3, py:"shí",  def:"time; hour" },
  { w:"明", r:72, rs:4, py:"míng", def:"bright; clear" },
  { w:"星", r:72, rs:5, py:"xīng", def:"star" },

  { w:"有", r:74, rs:2, py:"yǒu",  def:"to have; there is" },
  { w:"朋", r:74, rs:4, py:"péng", def:"friend" },
  { w:"期", r:74, rs:8, py:"qī",   def:"period; term" },

  { w:"林", r:75, rs:4, py:"lín",  def:"woods; forest" },
  { w:"树", r:75, rs:5, py:"shù",  def:"tree" },
  { w:"校", r:75, rs:6, py:"xiào", def:"school" },
  { w:"森", r:75, rs:8, py:"sēn",  def:"forest" },

  { w:"汉", r:85, rs:2, py:"hàn",  def:"Han (Chinese ethnicity/language)" },
  { w:"江", r:85, rs:3, py:"jiāng",def:"river" },
  { w:"河", r:85, rs:5, py:"hé",   def:"river" },
  { w:"海", r:85, rs:7, py:"hǎi",  def:"sea; ocean" },

  { w:"灯", r:86, rs:2, py:"dēng", def:"lamp; light" },
  { w:"热", r:86, rs:6, py:"rè",   def:"hot; heat" },
  { w:"烧", r:86, rs:6, py:"shāo", def:"to burn" },

  { w:"计", r:149,rs:2, py:"jì",   def:"to count; plan" },
  { w:"说", r:149,rs:7, py:"shuō", def:"to speak; to say" },
  { w:"话", r:149,rs:6, py:"huà",  def:"speech; words" },

  { w:"针", r:167,rs:2, py:"zhēn", def:"needle" },
  { w:"钱", r:167,rs:6, py:"qián", def:"money" },
  { w:"铁", r:167,rs:5, py:"tiě",  def:"iron" },
];
