#!/usr/bin/perl
#
#    SendmailAnalyzer: maillog parser and statistics reports tool for Sendmail
#    Copyright (C) 2002-2013 Gilles Darold
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
use strict qw(vars);

use CGI;

my $VERSION = '8.7';
my $COPYRIGHT = 'Copyright (c) 2002-2013 Gilles Darold - All rights reserved.';
my $AUTHOR = "Gilles Darold - gilles AT darold DOT net";
my $DEFAULT_TTFONT = '';

my $cgi = new CGI;

my @values = ();
push(@values, [ split(/:/, $cgi->param('labels')) ] );
my @legends = ();
foreach my $p (sort $cgi->param()) {
	if ($p =~ /^values/) {
		push(@values, [ split(/:/, $cgi->param($p)) ] );
	} elsif ($p =~ /^legend/) {
		push(@legends, $cgi->param($p));
	}
}
my $vertical = $cgi->param('vertical') || 0;
my $show_values = $cgi->param('show_values') || 0;
my $ttfont = $cgi->param('ttfont') || $DEFAULT_TTFONT;

print $cgi->header('image/png');

my $graph = '';
if (!$cgi->param('type') || ($cgi->param('type') eq 'area')) {
	use GD::Graph::bars3d;
	$graph = new GD::Graph::bars3d($cgi->param('width') || 400, $cgi->param('height') || 300);
	$graph->set( 
		x_label		=> $cgi->param('x_label') || '',
		y_label		=> $cgi->param('y_label') || '',
		title		=> $cgi->param('title') || '',
		fgclr		=> '#993300',
		legendclr	=> '#993300',
		dclrs		=> [ qw(lbrown lorange) ],
		x_labels_vertical => $vertical,
		long_ticks  => 1,
		shadow_depth => 5,
		box_axis => 0,
		show_values	=> $show_values,
	) or die $graph->error;
	if ($ttfont) {
		$graph->set_x_label_font($ttfont, 8);
		$graph->set_y_label_font($ttfont, 8);
		$graph->set_x_axis_font($ttfont, 8);
		$graph->set_y_axis_font($ttfont, 8);
		$graph->set_values_font($ttfont, 8);
	}
} elsif ($cgi->param('type') eq 'pie') {
	use GD::Graph::pie3d;
	$graph = new GD::Graph::pie3d($cgi->param('width') || 400, $cgi->param('height') || 300);
	$graph->set( 
		title	=> $cgi->param('title') || '',
		fgclr	=> '#993300',
		dclrs	=> [ qw(lbrown lorange lgray lyellow lgreen lblue lpurple lred) ],

	) or die $graph->error;
	if ($ttfont) {
		$graph->set_label_font($ttfont, 8);
		$graph->set_value_font($ttfont, 8);
	}
}

if ($ttfont) {
	$graph->set_title_font($ttfont, 12);
	$graph->set_legend_font($ttfont, 10);
}
$graph->set_text_clr('#993300');
$graph->set_legend(@legends) if ($#legends >= 0);

my $gd = $graph->plot(\@values) or die $graph->error;
print $gd->png;

exit 0;


