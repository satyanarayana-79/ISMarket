<?php
// Get latest report file
$files = glob("reports/report_*.json");
rsort($files);
$latest = $files[0] ?? null;

if ($latest) {
  $data = json_decode(file_get_contents($latest), true);
  $report_date = basename($latest, ".json");
} else {
  $data = [];
  $report_date = "No reports found";
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Daily Technical Analysis Report - <?php echo $report_date; ?></title>
<link rel="stylesheet" href="assets/style.css">
<script src="assets/script.js"></script>
</head>
<body>
<h1>Daily Technical Analysis Report (<?php echo $report_date; ?>)</h1>

<?php foreach ($data as $category => $stocks): ?>
  <h2><?php echo $category; ?></h2>
  <table>
    <thead>
      <tr>
        <th>Stock Name</th>
        <th>Price</th>
        <th>%Chg</th>
        <th>Volume</th>
        <th>Symbol</th>
      </tr>
    </thead>
    <tbody>
    <?php foreach ($stocks as $row): ?>
      <tr>
        <td><?php echo $row['Stock Name']; ?></td>
        <td><?php echo $row['Price']; ?></td>
        <td><?php echo $row['%Chg']; ?></td>
        <td><?php echo $row['Volume']; ?></td>
        <td><?php echo $row['Symbol']; ?></td>
      </tr>
    <?php endforeach; ?>
    </tbody>
  </table>
<?php endforeach; ?>

<footer>
  <p>© <?php echo date("Y"); ?> ismarket.in | Auto-updated trading insights</p>
</footer>
</body>
</html>
