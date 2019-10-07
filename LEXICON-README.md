# Lexicon

The lexicon is a tool that tells [Festival TTS](http://www.cstr.ed.ac.uk/projects/festival/) how to say certain words using
an easy-to-use script that makes use of the [CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict?).  
This script is then translated to a LISP script for each voice during generation.

## Phonemes

Each word in Festival is built from a simple set of syllables, and each syllable
is comprised of *phonemes*, which represent each distinct sound used for speech.

### CMU
The following table represents the current CMU Pronouncing Dictionary phonemes.

<table><thead><caption>Available Phonemes</caption><th>Phoneme</th><th>Example</th><th>Translation</th></thead>
<tbody>
<tr><th><code>AA</code></th><td>odd</td><td><code>"aa d"</code></tr>
<tr><th><code>AE</code></th><td>at</td><td><code>"ae t"</code></tr>
<tr><th><code>AH</code></th><td>hut</td><td><code>"hh ah t"</code></tr>
<tr><th><code>AO</code></th><td>ought</td><td><code>"ao t"</code></tr>
<tr><th><code>AW</code></th><td>cow</td><td><code>"k aw"</code></tr>
<tr><th><code>AY</code></th><td>hide</td><td><code>"hh ay d"</code></tr>
<tr><th><code>B</code></th><td>be</td><td><code>"b iy"</code></tr>
<tr><th><code>CH</code></th><td>cheese</td><td><code>"ch iy z"</code></tr>
<tr><th><code>D</code></th><td>dee</td><td><code>"d iy"</code></tr>
<tr><th><code>DH</code></th><td>thee</td><td><code>"dh iy"</code></tr>
<tr><th><code>EH</code></th><td>ed</td><td><code>"eh d"</code></tr>
<tr><th><code>EH</code></th><td>ed</td><td><code>"eh d"</code></tr>
<tr><th><code>ER</code></th><td>hurt</td><td><code>"hh er t"</code></tr>
<tr><th><code>EY</code></th><td>ate</td><td><code>"ey t"</code></tr>
<tr><th><code>F</code></th><td>fee</td><td><code>"f iy"</code></tr>
<tr><th><code>G</code></th><td>green</td><td><code>"g r iy n"</code></tr>
<tr><th><code>HH</code></th><td>he</td><td><code>"hh iy"</code></tr>
<tr><th><code>IH</code></th><td>it</td><td><code>"ih t"</code></tr>
<tr><th><code>IY</code></th><td>eat</td><td><code>"iy t"</code></tr>
<tr><th><code>JH</code></th><td>gee</td><td><code>"jh iy"</code></tr>
<tr><th><code>K</code></th><td>key</td><td><code>"k iy"</code></tr>
<tr><th><code>L</code></th><td>lee</td><td><code>"l iy"</code></tr>
<tr><th><code>M</code></th><td>me</td><td><code>"m iy"</code></tr>
<tr><th><code>N</code></th><td>knee</td><td><code>"n iy"</code></tr>
<tr><th><code>NG</code></th><td>ping</td><td><code>"p ih ng"</code></tr>
<tr><th><code>OW</code></th><td>oat</td><td><code>"ow t"</code></tr>
<tr><th><code>OY</code></th><td>toy</td><td><code>"t oy"</code></tr>
<tr><th><code>P</code></th><td>pee</td><td><code>"p iy"</code></tr>
<tr><th><code>R</code></th><td>read</td><td><code>"r iy d"</code></tr>
<tr><th><code>S</code></th><td>sea</td><td><code>"s iy"</code></tr>
<tr><th><code>SH</code></th><td>she</td><td><code>"sh iy"</code></tr>
<tr><th><code>T</code></th><td>tea</td><td><code>"t iy"</code></tr>
<tr><th><code>TH</code></th><td>theta</td><td><code>"th ey t ah"</code></tr>
<tr><th><code>UH</code></th><td>hood</td><td><code>"hh uh d"</code></tr>
<tr><th><code>UW</code></th><td>two</td><td><code>"t uw"</code></tr>
<tr><th><code>V</code></th><td>vee</td><td><code>"v iy"</code></tr>
<tr><th><code>W</code></th><td>we</td><td><code>"w iy"</code></tr>
<tr><th><code>Y</code></th><td>yield</td><td><code>"y iy l d"</code></tr>
<tr><th><code>Z</code></th><td>zee</td><td><code>"z iy"</code></tr>
<tr><th><code>ZH</code></th><td>seizure</td><td><code>"S IY" 'ZH ER'</code></tr>
</tbody>
</table>

### Other Known Phonemes
Some other phonemes that appear to work:

* <code>pau</code> - A short pause.
* <code>@</code> - Alias for <code>ae</code>? **Not used**, as it's non-standard and iffy with some voices.

## Emphasis

The lexicon supports emphasis as a number from 0 to 2, leaving us three levels of emphasis.

However, to simplify things, ss13-vox only supports 0 to 1, and uses the enclosing quote marks as the indicator of emphasis.

<table>
<tr><th>Quote Mark</th><th>Emphasis Level</th><th>Notes</th></tr>
<tr><th><code>"</code></th><td>1</td><td>Primary emphasis.</td></tr>
<tr><th><code>'</code></th><td>0</td><td>Secondary Emphasis.</td></tr>
</table>

In general, we try to code one Primary Emphasis into each word, leaving the rest without emphasis.
