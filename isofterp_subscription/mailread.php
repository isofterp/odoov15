<?
/** @package

      ReadMail.php
        
        Copyright(c) I-Soft Solutions 2002
        
        Author: R LAUTENBACH
        Created: RL  26-Jun-08 3:38:50 PM

Last change: RL 18-Jul-08  3:21:44 PM
Last change: QC 13-Nov-08 11:00:00 AM
*/

//read in params
$logfile    = $argv[1];
$mailserver = $argv[2];
$mailid     = $argv[3];
$mailpass   = $argv[4];

//chdir("logs"); 
//$logfile = date('ym')."_emailcontent.txt";
//$fp = fopen($logfile,"a"); //Open log file.If file does not exsist, attempt to create it
//chdir("..");


$fp = fopen($logfile,"a");

fwrite($fp,  "email,Reading,Clientcode,Contract No,Machine Type,Letter No\r\n");

//if (! ($mbox = imap_open ("{mail2.isoftnet.co.za:143}", "roly@isoft.co.za", "mark123"))) {
//      err_log("Can't open Mailbox for AppointMate");
//      exit();
// }

if (! ($mbox = imap_open ("{mail2.copytype.co.za}", "meterreadings@copytype.co.za" , "meter"))) {
      //err_log("Can't open Mailbox for AppointMate");
      fwrite($fp, "Can't open Mailbox for " . $mailid . "\r\n");
      exit();
}



//echo "<p><h3>Mail box opened for omnixsms</h3>\n";
//// This physically deletes emails that are set for deleteion.
imap_expunge($mbox);

$headers = imap_headers ($mbox);
//PRINT "We are here head=>$headers[0]<= <br>";

if ($headers == false) 
{ 
      //print  "<p><h3>No mail for omnixsms</h3>\n";
      fwrite($fp, "No mail found in mailbox\r\n");
      imap_close($mbox);
} 
else 
{
 while (list ($key,$val) = each ($headers)) 
 {
   $head = imap_header($mbox,$key + 1);
   if (strstr($head->subject, "Please submit machine meter readings") ) // Only open email for this system else delete it!   
   {                      
        $body           = imap_fetchbody($mbox,$key + 1,"1",FT_INTERNAL)."<br>\n<br>";  // Read in the body of the email
        $email_address  = $head->reply_to[0]->mailbox."@".$head->reply_to[0]->host;
    
        $reading     = "ReadingNotFound";
        $clientcode  = "ClientCodeNotFound";
        $contractno  = "ContractNoNotFound";
        $letterno    = "LetterNoNotFound";
        $typecode    = "MachineTypeNotFound";


         /*** Method 1 to extract data ***/
/*
         // tag_reading    >3000<
        if($start_pos  = strpos($body,"tag_reading"))                              // Find the Reading Tag and store its starting position
        {
           while($start_pos = strpos($body,">",$start_pos))                           // Find the Pos of the Meter Reading in next set of valid > < tags
           {  
              if(strpos("1234567890",substr($body,$start_pos + 1,1)))
              {
                 if($end_pos = strpos($body,"<",$start_pos))                             // Find the closing tag's position
                 {
                    $reading = substr($body,$start_pos + 1,$end_pos - $start_pos - 1);
                    break;
                 }
              }
              else
                 $start_pos++; 
           }
        }
        // tag_contractno    >10001<
        if($start_pos       = strpos($body,"tag_contractno")) {                         // Find the Reading Tag and store its starting position
           if($start_pos    = strpos($body,"||",$start_pos) + 1)  {                           // Find the Pos of the Meter Reading in next || || tags
             if($end_pos    = strpos($body,"||",$start_pos))                             // Find the closing tag's position
                $contractno = substr($body,$start_pos + 1,$end_pos - $start_pos - 1);
           }
        }
         // tag_clientcode >2525<
        if($start_pos      = strpos($body,"tag_clientcode")) {                          // Find the Cliet Code Tag and store its starting position
           if( $start_pos  = strpos($body,"||",$start_pos) + 1)  {                         // Find the Pos of the  Client Code in next || ||tags
            if($end_pos    = strpos($body,"||",$start_pos))                           // Find the closing tag's position
               $clientcode = substr($body,$start_pos + 1,$end_pos - $start_pos - 1);
            }
        }
*/



        /***QC: Method 2 to extract data ***/
        /*clean out gunk from body*/
        $body = str_replace("=20"," ",$body);
        $body = str_replace("3D","",$body);
        $body = str_replace("3d","",$body);
        $body = str_replace("&nbsp","",$body);
        $body = str_replace("&NBSP","",$body);
        $body = str_replace(";","",$body);

        /*1a. extract meter reading*/ 
        if(preg_match_all('/\>(\d\d+)\</',$body,$matches) > 0) //use regex to find meter reading
        {  
           $reading = substr($matches[0][1],1,strlen($matches[0][1]) - 2);
           $reading = str_replace(" ","",$reading);
        }
        /*1b. if pattern search didnt work then parse manually*/
        if(!is_numeric($reading))
        {
           $body2 = str_replace(" ","",$body);
           $numstart = false; 
           $reading2 = "";
           if($start_pos = strpos($body2,"*Currentmeterreading:"))
           { 
              $start_pos += 20;
              for($i=1;$i<1000;$i++)
              {
                 if(!is_numeric($body2{$start_pos + $i}))
                 { 
                    if(!$numstart)
                    {
                       continue;
                    }
                    else
                       break;
                 }
                 else 
                 if(is_numeric($body2{$start_pos + $i}))
                 { 
                    $numstart = true;
                    $reading2 .= "".$body2{$start_pos + $i}; 
                 }
              }
              if($reading2 > "")
                 $reading = $reading2;
              else
                 $reading = "Reading2 Not Found";                                                           
           }
        }
        /*2. extract client code*/ 
        if($start_pos = strpos($body,"||clientcode_"))
        { 
           $start_pos += 13;                                                           
           if($end_pos = strpos($body,"||",$start_pos))
              $clientcode = substr($body,$start_pos,($end_pos - $start_pos));
        }        
        /*3. extract contract no*/ 
        if($start_pos = strpos($body,"||contractno_"))
        { 
           $start_pos += 13;                                                           
           if($end_pos = strpos($body,"||",$start_pos))
              $contractno = substr($body,$start_pos,($end_pos - $start_pos));
        }
        /*4. extract letter no*/
        if($start_pos = strpos($body,"||letterno_"))
        { 
           $start_pos += 11;
           if($end_pos = strpos($body,"||",$start_pos))
              $letterno = substr($body,$start_pos,($end_pos - $start_pos));
        }
        /*5. extract machine type*/
        if($start_pos = strpos($body,"||typecode_"))
        { 
           $start_pos += 11;
           if($end_pos = strpos($body,"||",$start_pos))
              $typecode = substr($body,$start_pos,($end_pos - $start_pos));
        } 



        //Next two lines are for Debugging
        //print $body;
        //print "email," . $email_address . ",Reading," . $reading . ",Clientcode," . $clientcode . ",Contract No," . $contractno . ",Machine type," . $typecode . ",\n";
        fwrite($fp, $email_address . "," .  $reading . "," . $clientcode . "," . $contractno . "," . $typecode . "," . $letterno . "\r\n");
        imap_delete($mbox,$key + 1);  // Delete the eamil from the mailbox
   }
 }
}
?>
